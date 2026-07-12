"""Provider-agnostic LLM interface.

Everything the rest of the app needs from a language model is expressed here. Concrete
adapters (OpenAI, Anthropic, Gemini, OpenRouter, Ollama) implement `LLMProvider`; no
other package imports a vendor SDK or hits a vendor endpoint. Swapping providers is a
config change, never a code change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass
class ChatMessage:
    role: Role
    content: str


@dataclass
class ChatResult:
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)


@dataclass
class StreamChunk:
    delta: str
    done: bool = False


@dataclass
class ModelInfo:
    id: str
    label: str | None = None


@dataclass
class ConnectionStatus:
    ok: bool
    detail: str
    models_available: int | None = None


@dataclass
class ProviderConfig:
    """Everything needed to instantiate a provider for one request."""

    provider: str
    api_key: str | None = None
    chat_model: str = ""
    embedding_model: str | None = None
    base_url: str | None = None


class ProviderError(Exception):
    """Raised when a provider call fails or an operation is unsupported."""


class RateLimitError(ProviderError):
    """Raised when a provider is rate-limited / quota-exhausted (HTTP 429 or an
    equivalent soft-throttle). Signals that a fallback provider should be tried."""


class LLMProvider(ABC):
    """The contract every provider adapter fulfills."""

    name: str = "base"
    # Whether this provider offers an embeddings endpoint.
    supports_embeddings: bool = True

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    async def chat(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> ChatResult:
        """Return a single completion for the given messages."""

    @abstractmethod
    def stream(
        self, messages: Sequence[ChatMessage], *, model: str | None = None, **opts
    ) -> AsyncIterator[StreamChunk]:
        """Yield incremental completion chunks."""

    @abstractmethod
    async def embed(
        self, texts: Sequence[str], *, model: str | None = None
    ) -> list[list[float]]:
        """Return an embedding vector per input text."""

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List models available to the configured credentials."""

    @abstractmethod
    async def test_connection(self) -> ConnectionStatus:
        """Cheap round-trip that proves the credentials/endpoint work."""
