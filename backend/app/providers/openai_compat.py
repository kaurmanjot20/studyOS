"""Base adapter for OpenAI-compatible REST APIs.

OpenAI and OpenRouter expose the same surface (`/chat/completions`, `/models`,
`/embeddings`). This base implements it once; subclasses only set the base URL, auth
header, and any extra headers. Implemented with httpx so no vendor SDK is required.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence

import httpx

from app.providers.base import (
    ChatMessage,
    ChatResult,
    ConnectionStatus,
    LLMProvider,
    ModelInfo,
    ProviderError,
    StreamChunk,
)

_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


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
        }
        if "temperature" in opts:
            body["temperature"] = opts["temperature"]
        if "max_tokens" in opts:
            body["max_tokens"] = opts["max_tokens"]
        return body

    async def chat(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> ChatResult:
        model = model or self.config.chat_model
        body = self._payload(messages, model, **opts)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                self._url("/chat/completions"), headers=self._headers(), json=body
            )
        if resp.status_code >= 400:
            raise ProviderError(f"{self.name} chat failed: {resp.status_code} {resp.text[:300]}")
        data = resp.json()
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
        return ChatResult(content=choice, model=data.get("model", model), usage=usage)

    async def stream(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> AsyncIterator[StreamChunk]:
        model = model or self.config.chat_model
        body = self._payload(messages, model, **opts) | {"stream": True}
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            async with client.stream(
                "POST", self._url("/chat/completions"), headers=self._headers(), json=body
            ) as resp:
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

    async def embed(
        self, texts: Sequence[str], *, model: str | None = None
    ) -> list[list[float]]:
        model = model or self.config.embedding_model or ""
        if not model:
            raise ProviderError(f"{self.name}: no embedding model configured")
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                self._url("/embeddings"),
                headers=self._headers(),
                json={"model": model, "input": list(texts)},
            )
        if resp.status_code >= 400:
            raise ProviderError(
                f"{self.name} embed failed: {resp.status_code} {resp.text[:300]}"
            )
        data = resp.json()
        return [item["embedding"] for item in data["data"]]

    async def list_models(self) -> list[ModelInfo]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(self._url("/models"), headers=self._headers())
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
