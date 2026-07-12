"""Base adapter for OpenAI-compatible REST APIs.

OpenAI and OpenRouter expose the same surface (`/chat/completions`, `/models`,
`/embeddings`). This base implements it once; subclasses only set the base URL, auth
header, and any extra headers. Implemented with httpx so no vendor SDK is required.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Sequence

import httpx

from app.core.config import settings
from app.providers.base import (
    ChatMessage,
    ChatResult,
    ConnectionStatus,
    LLMProvider,
    ModelInfo,
    ProviderError,
    RateLimitError,
    StreamChunk,
)

_TIMEOUT = httpx.Timeout(60.0, connect=10.0)

# Transient statuses worth retrying with exponential backoff (rate limits, overload).
_RETRY_STATUS = {429, 503}
_MAX_ATTEMPTS = 4


def _backoff_seconds(attempt: int) -> float:
    return min(2**attempt, 8) + 0.25


async def _send_with_retry(
    client: httpx.AsyncClient, method: str, url: str, *, stream: bool = False, **kwargs
) -> httpx.Response:
    """Issue a request, retrying transient 429/503 with exponential backoff."""
    response: httpx.Response | None = None
    for attempt in range(_MAX_ATTEMPTS):
        request = client.build_request(method, url, **kwargs)
        response = await client.send(request, stream=stream)
        if response.status_code in _RETRY_STATUS and attempt < _MAX_ATTEMPTS - 1:
            await response.aclose()
            await asyncio.sleep(_backoff_seconds(attempt))
            continue
        return response
    assert response is not None
    return response


class OpenAICompatProvider(LLMProvider):
    base_url: str = ""

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _url(self, path: str) -> str:
        base = (self.config.base_url or self.base_url).rstrip("/")
        return f"{base}{path}"

    @staticmethod
    def _payload(messages: Sequence[ChatMessage], model: str, **opts) -> dict:
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            # Always bound completion length — required to stay within credit-limited
            # free tiers (e.g. OpenRouter), and a sane default everywhere else.
            "max_tokens": opts.get("max_tokens", settings.default_max_tokens),
        }
        if "temperature" in opts:
            body["temperature"] = opts["temperature"]
        return body

    async def chat(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> ChatResult:
        model = model or self.config.chat_model
        body = self._payload(messages, model, **opts)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # Some gateways soft-throttle bursts by returning 200 with empty choices;
            # retry those (and 429s, handled inside _send_with_retry) before giving up.
            for attempt in range(_MAX_ATTEMPTS):
                resp = await _send_with_retry(
                    client, "POST", self._url("/chat/completions"),
                    headers=self._headers(), json=body,
                )
                if resp.status_code == 429:
                    raise RateLimitError(f"{self.name} is rate-limited (429).")
                if resp.status_code >= 400:
                    raise ProviderError(
                        f"{self.name} chat failed: {resp.status_code} {resp.text[:300]}"
                    )
                data = resp.json()
                choices = data.get("choices") or []
                content = choices[0]["message"]["content"] if choices else ""
                if content:
                    return ChatResult(
                        content=content,
                        model=data.get("model", model),
                        usage=data.get("usage") or {},
                    )
                await asyncio.sleep(_backoff_seconds(attempt))
        # Exhausted retries with only empty responses — treat as a soft rate limit.
        raise RateLimitError(f"{self.name} returned no content (soft rate limit).")

    async def stream(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> AsyncIterator[StreamChunk]:
        model = model or self.config.chat_model
        body = self._payload(messages, model, **opts) | {"stream": True}
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await _send_with_retry(
                client, "POST", self._url("/chat/completions"),
                stream=True, headers=self._headers(), json=body,
            )
            try:
                if resp.status_code == 429:
                    await resp.aread()
                    raise RateLimitError(f"{self.name} is rate-limited (429).")
                if resp.status_code >= 400:
                    text = await resp.aread()
                    raise ProviderError(
                        f"{self.name} stream failed: {resp.status_code} {text[:300]!r}"
                    )
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        yield StreamChunk(delta="", done=True)
                        return
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
                    if delta:
                        yield StreamChunk(delta=delta)
            finally:
                await resp.aclose()

    async def embed(
        self, texts: Sequence[str], *, model: str | None = None
    ) -> list[list[float]]:
        model = model or self.config.embedding_model or ""
        if not model:
            raise ProviderError(f"{self.name}: no embedding model configured")
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await _send_with_retry(
                client, "POST", self._url("/embeddings"),
                headers=self._headers(),
                json={"model": model, "input": list(texts)},
            )
        if resp.status_code == 429:
            raise RateLimitError(f"{self.name} is rate-limited (429).")
        if resp.status_code >= 400:
            raise ProviderError(
                f"{self.name} embed failed: {resp.status_code} {resp.text[:300]}"
            )
        data = resp.json()
        return [item["embedding"] for item in data["data"]]

    async def list_models(self) -> list[ModelInfo]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await _send_with_retry(
                client, "GET", self._url("/models"), headers=self._headers()
            )
        if resp.status_code >= 400:
            raise ProviderError(
                f"{self.name} list_models failed: {resp.status_code} {resp.text[:200]}"
            )
        data = resp.json()
        items = data.get("data", data if isinstance(data, list) else [])
        return [ModelInfo(id=m["id"]) for m in items if isinstance(m, dict) and "id" in m]

    async def test_connection(self) -> ConnectionStatus:
        try:
            models = await self.list_models()
        except ProviderError as exc:
            return ConnectionStatus(ok=False, detail=str(exc))
        except httpx.HTTPError as exc:
            return ConnectionStatus(ok=False, detail=f"Network error: {exc}")
        return ConnectionStatus(
            ok=True,
            detail=f"Connected to {self.name}.",
            models_available=len(models),
        )
