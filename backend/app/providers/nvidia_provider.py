"""NVIDIA NIM adapter (OpenAI-compatible REST).

NVIDIA's hosted inference API (`integrate.api.nvidia.com/v1`) speaks the OpenAI schema,
so chat/stream/model-listing come straight from the compat base. Embeddings need one
extra field (`input_type`) that OpenAI does not use, so `embed` is overridden.
"""

from __future__ import annotations

from collections.abc import Sequence

import httpx

from app.providers.base import ProviderError
from app.providers.openai_compat import _send_with_retry, OpenAICompatProvider

_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class NvidiaProvider(OpenAICompatProvider):
    name = "nvidia"
    base_url = "https://integrate.api.nvidia.com/v1"

    async def embed(
        self, texts: Sequence[str], *, model: str | None = None
    ) -> list[list[float]]:
        model = model or self.config.embedding_model or ""
        if not model:
            raise ProviderError("nvidia: no embedding model configured")
        # NVIDIA embedding NIMs require input_type; "passage" indexes documents.
        payload = {
            "model": model,
            "input": list(texts),
            "input_type": "passage",
            "truncate": "END",
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await _send_with_retry(
                client, "POST", self._url("/embeddings"),
                headers=self._headers(), json=payload,
            )
        if resp.status_code >= 400:
            raise ProviderError(
                f"nvidia embed failed: {resp.status_code} {resp.text[:300]}"
            )
        data = resp.json()
        return [item["embedding"] for item in data["data"]]
