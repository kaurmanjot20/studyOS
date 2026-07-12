"""Mock interview session model.

A session holds its configuration and a JSONB transcript of turns. Each turn is
{question, topic, answer?, score?, feedback?}. Keeping the transcript inline keeps the
conductor simple; sessions are short and read as a unit.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class InterviewSession(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "interview_sessions"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company: Mapped[str | None] = mapped_column(String(120), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(160), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active | completed
    target_questions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    asked_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Overall score (0-100) once completed.
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    # [{question, topic, answer?, score?, feedback?}]
    transcript: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
