"""Google Gemini adapter (native Generative Language API).

Notes specific to Gemini:
- Roles are `user` and `model` (assistant maps to `model`); system prompts go in
  `systemInstruction`.
- The API key is a query parameter, not a bearer token.
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
_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _norm(model: str) -> str:
    return model.removeprefix("models/")


class GeminiProvider(LLMProvider):
    name = "gemini"

    @staticmethod
    def _contents(messages: Sequence[ChatMessage]) -> tuple[dict | None, list[dict]]:
        system_parts = [m.content for m in messages if m.role == "system"]
        contents = [
            {
                "role": "model" if m.role == "assistant" else "user",
                "parts": [{"text": m.content}],
            }
            for m in messages
            if m.role in ("user", "assistant")
        ]
        system = (
            {"parts": [{"text": "\n\n".join(system_parts)}]} if system_parts else None
        )
        return system, contents

    def _body(self, messages: Sequence[ChatMessage], **opts) -> dict:
        system, contents = self._contents(messages)
        body: dict = {"contents": contents}
        if system:
            body["systemInstruction"] = system
        gen: dict = {}
        if "temperature" in opts:
            gen["temperature"] = opts["temperature"]
        if "max_tokens" in opts:
            gen["maxOutputTokens"] = opts["max_tokens"]
        if gen:
            body["generationConfig"] = gen
        return body

    def _key(self) -> str:
        if not self.config.api_key:
            raise ProviderError("gemini: no API key configured")
        return self.config.api_key

    async def chat(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> ChatResult:
        model = _norm(model or self.config.chat_model)
        url = f"{_BASE}/models/{model}:generateContent?key={self._key()}"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json=self._body(messages, **opts))
        if resp.status_code >= 400:
            raise ProviderError(f"gemini chat failed: {resp.status_code} {resp.text[:300]}")
        data = resp.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)
        return ChatResult(content=text, model=model)

    async def stream(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> AsyncIterator[StreamChunk]:
        model = _norm(model or self.config.chat_model)
        url = f"{_BASE}/models/{model}:streamGenerateContent?alt=sse&key={self._key()}"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            async with client.stream("POST", url, json=self._body(messages, **opts)) as resp:
                if resp.status_code >= 400:
                    await resp.aread()
                    raise ProviderError(f"gemini stream failed: {resp.status_code}")
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[len("data:") :].strip()
                    if not payload:
                        continue
                    try:
                        event = json.loads(payload)
                        parts = (
                            event.get("candidates", [{}])[0]
                            .get("content", {})
                            .get("parts", [])
                        )
                        delta = "".join(p.get("text", "") for p in parts)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
                    if delta:
                        yield StreamChunk(delta=delta)
        yield StreamChunk(delta="", done=True)

    async def embed(
        self, texts: Sequence[str], *, model: str | None = None
    ) -> list[list[float]]:
        model = _norm(model or self.config.embedding_model or "text-embedding-004")
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for text in texts:
                url = f"{_BASE}/models/{model}:embedContent?key={self._key()}"
                resp = await client.post(
                    url, json={"content": {"parts": [{"text": text}]}}
                )
                if resp.status_code >= 400:
                    raise ProviderError(
                        f"gemini embed failed: {resp.status_code} {resp.text[:200]}"
                    )
                vectors.append(resp.json()["embedding"]["values"])
        return vectors

    async def list_models(self) -> list[ModelInfo]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{_BASE}/models?key={self._key()}")
        if resp.status_code >= 400:
            raise ProviderError(
                f"gemini list_models failed: {resp.status_code} {resp.text[:200]}"
            )
        data = resp.json()
        return [
            ModelInfo(id=_norm(m["name"]))
            for m in data.get("models", [])
            if "name" in m
        ]

    async def test_connection(self) -> ConnectionStatus:
        try:
            models = await self.list_models()
        except ProviderError as exc:
            return ConnectionStatus(ok=False, detail=str(exc))
        except httpx.HTTPError as exc:
            return ConnectionStatus(ok=False, detail=f"Network error: {exc}")
        return ConnectionStatus(
            ok=True, detail="Connected to Gemini.", models_available=len(models)
        )
