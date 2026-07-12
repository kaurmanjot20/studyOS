"""Global search across workspaces, documents, and chat sessions.

A lightweight case-insensitive substring search used by the top-bar command palette.
Returns navigable results grouped by type.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatSession
from app.models.document import Document
from app.models.workspace import Workspace

_LIMIT = 8


class SearchService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(self, query: str) -> dict:
        q = query.strip()
        if not q:
            return {"workspaces": [], "documents": [], "chats": []}
        like = f"%{q}%"

        ws_rows = (
            await self.db.execute(
                select(Workspace)
                .where(Workspace.name.ilike(like))
                .order_by(Workspace.name)
                .limit(_LIMIT)
            )
        ).scalars().all()

        doc_rows = (
            await self.db.execute(
                select(Document)
                .where(Document.filename.ilike(like) | Document.title.ilike(like))
                .order_by(Document.created_at.desc())
                .limit(_LIMIT)
            )
        ).scalars().all()

        chat_rows = (
            await self.db.execute(
                select(ChatSession)
                .where(ChatSession.title.ilike(like))
                .order_by(ChatSession.created_at.desc())
                .limit(_LIMIT)
            )
        ).scalars().all()

        return {
            "workspaces": [{"id": str(w.id), "label": w.name} for w in ws_rows],
            "documents": [
                {
                    "id": str(d.id),
                    "workspace_id": str(d.workspace_id),
                    "label": d.title or d.filename,
                }
                for d in doc_rows
            ],
            "chats": [
                {
                    "id": str(c.id),
                    "workspace_id": str(c.workspace_id),
                    "label": c.title or "Untitled chat",
                }
                for c in chat_rows
            ],
        }
