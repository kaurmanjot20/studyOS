"""OpenAI adapter (OpenAI-compatible REST)."""

from __future__ import annotations

from app.providers.openai_compat import OpenAICompatProvider


class OpenAIProvider(OpenAICompatProvider):
    name = "openai"
    base_url = "https://api.openai.com/v1"
