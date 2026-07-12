"""Retrieval and context assembly.

Embeds the (rewritten) query through the provider abstraction and runs a workspace-scoped
cosine-similarity search over pgvector, then assembles the top chunks into a numbered
context block the synthesizer can cite.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import RetrievedChunk
from app.models.document import Chunk, Document
from app.providers.base import LLMProvider


async def retrieve(
    db: AsyncSession,
    provider: LLMProvider,
    *,
    workspace_id: uuid.UUID,
    query: str,
    embedding_model: str,
    k: int = 6,
) -> list[RetrievedChunk]:
    query_vec = (await provider.embed([query], model=embedding_model))[0]

    distance = Chunk.embedding.cosine_distance(query_vec)
    stmt = (
        select(
            Chunk.document_id,
            Chunk.content,
            Chunk.page,
            Document.filename,
            distance.label("distance"),
        )
        .join(Document, Chunk.document_id == Document.id)
        .where(
            Chunk.workspace_id == workspace_id,
            Chunk.embedding.isnot(None),
        )
        .order_by(distance)
        .limit(k)
    )
    rows = (await db.execute(stmt)).all()
    return [
        RetrievedChunk(
            document_id=document_id,
            filename=filename,
            page=page,
            content=content,
            score=round(1.0 - float(dist), 4),
        )
        for document_id, content, page, filename, dist in rows
    ]


def assemble_context(chunks: list[RetrievedChunk]) -> str:
    blocks: list[str] = []
    for i, ch in enumerate(chunks, start=1):
        location = ch.filename + (f", p.{ch.page}" if ch.page else "")
        blocks.append(f"[{i}] (source: {location})\n{ch.content.strip()}")
    return "\n\n".join(blocks)
