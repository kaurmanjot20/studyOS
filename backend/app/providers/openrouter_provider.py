"""OpenRouter adapter (OpenAI-compatible REST).

OpenRouter proxies many providers behind the OpenAI schema. Embeddings are not offered
across the board, so callers should pick a dedicated embedding provider for RAG.
"""

from __future__ import annotations

from app.providers.openai_compat import OpenAICompatProvider


class OpenRouterProvider(OpenAICompatProvider):
    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"
    supports_embeddings = False

    def _headers(self) -> dict[str, str]:
        headers = super()._headers()
        # Optional attribution headers recommended by OpenRouter.
        headers["HTTP-Referer"] = "https://github.com/kaurmanjot20/studyOS"
        headers["X-Title"] = "InterviewOS"
        return headers
