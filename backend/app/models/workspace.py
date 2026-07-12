"""Workspace model.

A workspace is a top-level knowledge-base container (e.g. "Operating Systems",
"Interview Preparation"). Documents, chats, quizzes, and memory all hang off a
workspace. The app is single-user, so workspaces are not owned by an account.
"""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Workspace(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optional subject tag (e.g. "DBMS") used for grouping in the sidebar.
    subject: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # A small accent hint for the UI (hex or token name); purely presentational.
    color: Mapped[str | None] = mapped_column(String(24), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Workspace id={self.id} name={self.name!r}>"
