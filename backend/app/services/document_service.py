"""Document pipeline business logic.

Handles upload persistence, listing, deletion, and the background processing pipeline:
extract → chunk → embed (via the provider abstraction) → store. Processing runs in a
FastAPI background task with its own DB session, updating the document's status so the UI
can reflect progress live.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import SessionFactory
from app.models.document import Chunk, Document, DocumentStatus
from app.providers.base import ProviderError
from app.providers.factory import build_provider
from app.rag.chunking import chunk_document
from app.rag.extraction import UnsupportedFileType, extract
from app.services.provider_service import ProviderService
from app.services import storage


class DocumentNotFound(Exception):
    def __init__(self, document_id: uuid.UUID) -> None:
        super().__init__(f"Document {document_id} not found")
        self.document_id = document_id


class DocumentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        workspace_id: uuid.UUID,
        filename: str,
        content_type: str | None,
        data: bytes,
    ) -> Document:
        document_id = uuid.uuid4()
        path, size = storage.save_upload(workspace_id, document_id, filename, data)
        doc = Document(
            id=document_id,
            workspace_id=workspace_id,
            filename=filename,
            content_type=content_type,
            file_path=path,
            size_bytes=size,
            status=DocumentStatus.queued.value,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def list(self, workspace_id: uuid.UUID) -> list[Document]:
        result = await self.db.execute(
            select(Document)
            .where(Document.workspace_id == workspace_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, document_id: uuid.UUID) -> Document:
        doc = await self.db.get(Document, document_id)
        if doc is None:
            raise DocumentNotFound(document_id)
        return doc

    async def delete(self, document_id: uuid.UUID) -> None:
        doc = await self.get(document_id)
        storage.delete_file(doc.file_path)
        await self.db.delete(doc)
        await self.db.commit()


async def process_document(document_id: uuid.UUID) -> None:
    """Background pipeline. Owns its own session (runs after the request returns)."""
    async with SessionFactory() as db:
        doc = await db.get(Document, document_id)
        if doc is None:
            return
        doc.status = DocumentStatus.processing.value
        doc.error = None
        await db.commit()

        try:
            extracted = extract(doc.file_path, doc.filename)
            chunks = chunk_document(extracted)

            if not chunks:
                doc.status = DocumentStatus.ready.value
                doc.title = extracted.title
                doc.page_count = extracted.page_count
                doc.word_count = extracted.word_count
                doc.chunk_count = 0
                await db.commit()
                return

            emb_config = await ProviderService(db).resolve_embedding_config()
            if not emb_config.embedding_model:
                raise ProviderError(
                    "No embedding model configured. Set one in AI Provider Settings."
                )
            embedder = build_provider(emb_config)

            vectors = await _embed_all(
                [c.content for c in chunks], embedder, emb_config.embedding_model
            )
            _validate_dims(vectors)

            for chunk, vector in zip(chunks, vectors):
                db.add(
                    Chunk(
                        document_id=doc.id,
                        workspace_id=doc.workspace_id,
                        ordinal=chunk.ordinal,
                        content=chunk.content,
                        page=chunk.page,
                        char_start=chunk.char_start,
                        char_end=chunk.char_end,
                        embedding=vector,
                    )
                )

            doc.title = extracted.title
            doc.page_count = extracted.page_count
            doc.word_count = extracted.word_count
            doc.chunk_count = len(chunks)
            doc.embedding_model = emb_config.embedding_model
            doc.embedding_dim = len(vectors[0])
            doc.status = DocumentStatus.ready.value
            await db.commit()

        except (UnsupportedFileType, ProviderError) as exc:
            await _fail(db, document_id, str(exc))
        except Exception as exc:  # pragma: no cover - defensive catch-all
            await _fail(db, document_id, f"Processing failed: {exc}")


async def _embed_all(texts: list[str], provider, model: str) -> list[list[float]]:
    vectors: list[list[float]] = []
    batch = settings.embed_batch_size
    for i in range(0, len(texts), batch):
        vectors.extend(await provider.embed(texts[i : i + batch], model=model))
    return vectors


def _validate_dims(vectors: list[list[float]]) -> None:
    if vectors and len(vectors[0]) != settings.embedding_dim:
        raise ProviderError(
            f"Embedding dimension {len(vectors[0])} does not match the configured "
            f"EMBEDDING_DIM={settings.embedding_dim}. Set EMBEDDING_DIM to match your "
            f"embedding model and re-run migrations, then re-upload."
        )


async def _fail(db: AsyncSession, document_id: uuid.UUID, message: str) -> None:
    # Discard any half-added chunks from the failed run before recording the error.
    await db.rollback()
    doc = await db.get(Document, document_id)
    if doc is None:
        return
    doc.status = DocumentStatus.failed.value
    doc.error = message
    await db.commit()
