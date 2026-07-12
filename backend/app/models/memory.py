"""Memory model.

Long-term memory the planner consults before answering. Three kinds:
- `weak_topic`: a subject the learner repeatedly struggles with (weight = miss count),
  populated by quiz/interview scoring; drives revision prioritization.
- `preference`: how the learner likes to be helped (e.g. "prefers concise answers").
- `note`: any other durable fact worth remembering about the learner.
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class MemoryKind(str, enum.Enum):
    weak_topic = "weak_topic"
    preference = "preference"
    note = "note"


class Memory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "memories"
    __table_args__ = (
        # One weak-topic row per (workspace, topic) so misses accumulate on it.
        UniqueConstraint("workspace_id", "kind", "topic", name="uq_memory_topic"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    # Set for weak_topic (the subject name); null for preferences/notes.
    topic: Mapped[str | None] = mapped_column(String(160), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Importance / miss count. Higher = surfaced first.
    weight: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
