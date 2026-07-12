"""Provider registry and factory.

The single choke point where a provider name becomes a concrete `LLMProvider`. The rest
of the app calls `build_provider(config)` and never imports an adapter directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import LLMProvider, ProviderConfig
from app.providers.gemini_provider import GeminiProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.openrouter_provider import OpenRouterProvider

_REGISTRY: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "openrouter": OpenRouterProvider,
    "ollama": OllamaProvider,
}


@dataclass(frozen=True)
class ProviderMeta:
    name: str
    label: str
    requires_api_key: bool
    supports_embeddings: bool
    default_base_url: str | None = None


PROVIDER_META: dict[str, ProviderMeta] = {
    "openai": ProviderMeta("openai", "OpenAI", True, True),
    "anthropic": ProviderMeta("anthropic", "Anthropic", True, False),
    "gemini": ProviderMeta("gemini", "Google Gemini", True, True),
    "openrouter": ProviderMeta("openrouter", "OpenRouter", True, False),
    "ollama": ProviderMeta(
        "ollama", "Ollama (local)", False, True, "http://localhost:11434"
    ),
}


def available_providers() -> list[ProviderMeta]:
    return list(PROVIDER_META.values())


def build_provider(config: ProviderConfig) -> LLMProvider:
    try:
        provider_cls = _REGISTRY[config.provider]
    except KeyError:
        raise ValueError(f"Unknown provider: {config.provider!r}")
    return provider_cls(config)
