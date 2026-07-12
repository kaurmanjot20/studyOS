"""Chat persistence business logic: sessions and messages."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatSession, Message


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_session(
        self,
        workspace_id: uuid.UUID,
        session_id: uuid.UUID | None = None,
        title: str | None = None,
    ) -> ChatSession:
        if session_id is not None:
            session = await self.db.get(ChatSession, session_id)
            if session is not None:
                return session
        session = ChatSession(workspace_id=workspace_id, title=title)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def add_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        *,
        sources: list | None = None,
        plan: dict | None = None,
    ) -> Message:
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            sources=sources,
            plan=plan,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def list_sessions(self, workspace_id: uuid.UUID) -> list[ChatSession]:
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.workspace_id == workspace_id)
            .order_by(ChatSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_messages(self, session_id: uuid.UUID) -> list[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())

    async def rename_session(
        self, session_id: uuid.UUID, title: str
    ) -> ChatSession | None:
        session = await self.db.get(ChatSession, session_id)
        if session is None:
            return None
        session.title = title.strip() or session.title
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def delete_session(self, session_id: uuid.UUID) -> None:
        session = await self.db.get(ChatSession, session_id)
        if session is not None:
            await self.db.delete(session)
            await self.db.commit()
