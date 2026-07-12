"""Fallback provider.

Wraps a primary provider and a fallback provider behind the same `LLMProvider`
interface. When the primary raises `RateLimitError` (HTTP 429 or a soft throttle), the
call is transparently retried on the fallback — typically a local Ollama model, so the
app keeps working when a hosted free tier runs out of quota.

The fallback is called with its own configured model (not the primary's model name),
since a local model won't recognise e.g. an OpenRouter model id.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from app.providers.base import (
    ChatMessage,
    ChatResult,
    ConnectionStatus,
    LLMProvider,
    ProviderConfig,
    ProviderError,
    RateLimitError,
    StreamChunk,
)


def _fallback_unavailable(primary: str, fallback: str, error: Exception) -> ProviderError:
    return ProviderError(
        f"{primary} is rate-limited and the local fallback ({fallback}) is not "
        f"reachable ({str(error)[:120]}). Start Ollama (and `ollama pull` the fallback "
        f"model), switch to a less-limited model in Settings, or retry shortly."
    )


class FallbackProvider(LLMProvider):
    name = "fallback"

    def __init__(self, primary: LLMProvider, fallback: LLMProvider) -> None:
        # A synthetic config; the wrapped providers carry the real ones.
        super().__init__(ProviderConfig(provider="fallback"))
        self.primary = primary
        self.fallback = fallback
        self.supports_embeddings = primary.supports_embeddings

    async def chat(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> ChatResult:
        try:
            return await self.primary.chat(messages, model=model, **opts)
        except RateLimitError:
            # Fallback uses its own configured model.
            try:
                return await self.fallback.chat(messages, **opts)
            except Exception as exc:
                raise _fallback_unavailable(
                    self.primary.name, self.fallback.name, exc
                ) from exc

    async def stream(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> AsyncIterator[StreamChunk]:
        # Try to open the primary stream; if it rate-limits before producing any
        # output, switch to the fallback. (Our adapters raise on open, before the
        # first token, so this cleanly covers the throttle case.)
        primary_iter = self.primary.stream(messages, model=model, **opts)
        try:
            first = await primary_iter.__anext__()
        except StopAsyncIteration:
            return
        except RateLimitError:
            try:
                async for chunk in self.fallback.stream(messages, **opts):
                    yield chunk
            except Exception as exc:
                raise _fallback_unavailable(
                    self.primary.name, self.fallback.name, exc
                ) from exc
            return

        yield first
        async for chunk in primary_iter:
            yield chunk

    async def embed(
        self, texts: Sequence[str], *, model: str | None = None
    ) -> list[list[float]]:
        try:
            return await self.primary.embed(texts, model=model)
        except RateLimitError:
            return await self.fallback.embed(texts)

    async def list_models(self):
        return await self.primary.list_models()

    async def test_connection(self) -> ConnectionStatus:
        return await self.primary.test_connection()
