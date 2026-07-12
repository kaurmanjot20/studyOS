"""Ollama adapter (native local API).

Talks to a local Ollama server (default http://localhost:11434). Uses Ollama's native
endpoints rather than its OpenAI-compat shim so model listing and embeddings work
reliably against local installs.
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

_TIMEOUT = httpx.Timeout(120.0, connect=10.0)
_DEFAULT_BASE = "http://localhost:11434"


class OllamaProvider(LLMProvider):
    name = "ollama"

    def _base(self) -> str:
        return (self.config.base_url or _DEFAULT_BASE).rstrip("/")

    async def chat(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> ChatResult:
        model = model or self.config.chat_model
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(f"{self._base()}/api/chat", json=body)
        if resp.status_code >= 400:
            raise ProviderError(f"ollama chat failed: {resp.status_code} {resp.text[:300]}")
        data = resp.json()
        return ChatResult(content=data["message"]["content"], model=model)

    async def stream(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> AsyncIterator[StreamChunk]:
        model = model or self.config.chat_model
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            async with client.stream("POST", f"{self._base()}/api/chat", json=body) as resp:
                if resp.status_code >= 400:
                    text = await resp.aread()
                    raise ProviderError(f"ollama stream failed: {resp.status_code}")
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if chunk.get("done"):
                        yield StreamChunk(delta="", done=True)
                        return
                    delta = chunk.get("message", {}).get("content", "")
                    if delta:
                        yield StreamChunk(delta=delta)

    async def embed(
        self, texts: Sequence[str], *, model: str | None = None
    ) -> list[list[float]]:
        model = model or self.config.embedding_model or self.config.chat_model
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for text in texts:
                resp = await client.post(
                    f"{self._base()}/api/embeddings",
                    json={"model": model, "prompt": text},
                )
                if resp.status_code >= 400:
                    raise ProviderError(
                        f"ollama embed failed: {resp.status_code} {resp.text[:200]}"
                    )
                vectors.append(resp.json()["embedding"])
        return vectors

    async def list_models(self) -> list[ModelInfo]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{self._base()}/api/tags")
        if resp.status_code >= 400:
            raise ProviderError(f"ollama list_models failed: {resp.status_code}")
        data = resp.json()
        return [ModelInfo(id=m["name"]) for m in data.get("models", [])]

    async def test_connection(self) -> ConnectionStatus:
        try:
            models = await self.list_models()
        except (ProviderError, httpx.HTTPError) as exc:
            return ConnectionStatus(
                ok=False,
                detail=f"Could not reach Ollama at {self._base()}: {exc}",
            )
        return ConnectionStatus(
            ok=True, detail="Connected to Ollama.", models_available=len(models)
        )
