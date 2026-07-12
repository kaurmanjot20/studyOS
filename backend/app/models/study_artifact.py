"""Saved study artifact.

Persists generated quizzes, flashcard sets, revision notes, and resume outputs so each
study tab has a browsable history. The generated content is stored verbatim in `payload`
(JSONB) and rendered back when a past artifact is reopened.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class StudyArtifact(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "study_artifacts"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # quiz | flashcards | revision | resume_review | resume_questions
    kind: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
