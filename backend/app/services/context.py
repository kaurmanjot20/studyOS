"""Shared retrieval helper.

Resolves the embedding provider and returns assembled RAG context for a query, or an
empty string if embeddings are unavailable. Used by generators (interview, study) that
want their output grounded in the workspace's documents.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.factory import build_provider
from app.rag.retrieval import assemble_context, retrieve
from app.services.provider_service import ProviderService


async def build_context(
    db: AsyncSession, workspace_id: uuid.UUID, query: str, *, k: int = 8
) -> str:
    emb_config = await ProviderService(db).resolve_embedding_config()
    if not emb_config.embedding_model:
        return ""
    try:
        embedder = build_provider(emb_config)
        chunks = await retrieve(
            db,
            embedder,
            workspace_id=workspace_id,
            query=query,
            embedding_model=emb_config.embedding_model,
            k=k,
        )
        return assemble_context(chunks)
    except Exception:
        return ""
