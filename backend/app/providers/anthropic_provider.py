"""Anthropic adapter (native Messages API).

Notes specific to Anthropic:
- `system` is a top-level parameter, not a message role, so system turns are split out.
- `max_tokens` is required; we default it when the caller doesn't pass one.
- There is no embeddings endpoint — `embed` raises and callers pick another provider.
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
_BASE = "https://api.anthropic.com/v1"
_VERSION = "2023-06-01"
_DEFAULT_MAX_TOKENS = 1024


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    supports_embeddings = False

    def _headers(self) -> dict[str, str]:
        return {
            "content-type": "application/json",
            "x-api-key": self.config.api_key or "",
            "anthropic-version": _VERSION,
        }

    @staticmethod
    def _split(messages: Sequence[ChatMessage]) -> tuple[str | None, list[dict]]:
        system_parts = [m.content for m in messages if m.role == "system"]
        turns = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        system = "\n\n".join(system_parts) if system_parts else None
        return system, turns

    def _body(self, messages: Sequence[ChatMessage], model: str, **opts) -> dict:
        system, turns = self._split(messages)
        body: dict = {
            "model": model,
            "messages": turns,
            "max_tokens": opts.get("max_tokens", _DEFAULT_MAX_TOKENS),
        }
        if system:
            body["system"] = system
        if "temperature" in opts:
            body["temperature"] = opts["temperature"]
        return body

    async def chat(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> ChatResult:
        model = model or self.config.chat_model
        body = self._body(messages, model, **opts)
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(f"{_BASE}/messages", headers=self._headers(), json=body)
        if resp.status_code >= 400:
            raise ProviderError(f"anthropic chat failed: {resp.status_code} {resp.text[:300]}")
        data = resp.json()
        text = "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        )
        usage = {
            "input_tokens": data.get("usage", {}).get("input_tokens", 0),
            "output_tokens": data.get("usage", {}).get("output_tokens", 0),
        }
        return ChatResult(content=text, model=data.get("model", model), usage=usage)

    async def stream(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> AsyncIterator[StreamChunk]:
        model = model or self.config.chat_model
        body = self._body(messages, model, **opts) | {"stream": True}
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            async with client.stream(
                "POST", f"{_BASE}/messages", headers=self._headers(), json=body
            ) as resp:
                if resp.status_code >= 400:
                    text = await resp.aread()
                    raise ProviderError(f"anthropic stream failed: {resp.status_code}")
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[len("data:") :].strip()
                    if not payload:
                        continue
                    try:
                        event = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    etype = event.get("type")
                    if etype == "content_block_delta":
                        delta = event.get("delta", {}).get("text", "")
                        if delta:
                            yield StreamChunk(delta=delta)
                    elif etype == "message_stop":
                        yield StreamChunk(delta="", done=True)
                        return

    async def embed(
        self, texts: Sequence[str], *, model: str | None = None
    ) -> list[list[float]]:
        raise ProviderError(
            "Anthropic has no embeddings API. Configure a different embedding provider "
            "(e.g. OpenAI, Gemini, or Ollama) for retrieval."
        )

    async def list_models(self) -> list[ModelInfo]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{_BASE}/models", headers=self._headers())
        if resp.status_code >= 400:
            raise ProviderError(
                f"anthropic list_models failed: {resp.status_code} {resp.text[:200]}"
            )
        data = resp.json()
        return [ModelInfo(id=m["id"]) for m in data.get("data", []) if "id" in m]

    async def test_connection(self) -> ConnectionStatus:
        try:
            models = await self.list_models()
        except ProviderError as exc:
            return ConnectionStatus(ok=False, detail=str(exc))
        except httpx.HTTPError as exc:
            return ConnectionStatus(ok=False, detail=f"Network error: {exc}")
        return ConnectionStatus(
            ok=True, detail="Connected to Anthropic.", models_available=len(models)
        )
