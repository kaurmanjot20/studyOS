"""Document and chunk models.

A `Document` is an uploaded file that moves through the processing pipeline
(queued → processing → ready / failed). Its extracted text is split into `Chunk`s,
each carrying a pgvector embedding plus the provenance needed for citation (page and
character span).
"""

from __future__ import annotations

import enum
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base, TimestampMixin, UUIDMixin


class DocumentStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class Document(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Stored as the plain enum *value* ("queued", "ready", ...) for stable serialization.
    status: Mapped[str] = mapped_column(
        String(20), default=DocumentStatus.queued.value, nullable=False
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Extracted metadata.
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Which embedding produced this document's vectors (for dim-mismatch handling).
    embedding_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    embedding_dim: Mapped[int | None] = mapped_column(Integer, nullable=True)

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Chunk(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Ordinal position of the chunk within its document.
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Provenance for citations.
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dim), nullable=True
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")
