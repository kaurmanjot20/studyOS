"""Memory business logic.

Records and retrieves long-term memory, and produces a compact summary the planner reads
before deciding how to answer — so revision naturally prioritizes weak topics and answers
respect stated preferences.
"""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory, MemoryKind


class MemoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_weak_topic(
        self, workspace_id: uuid.UUID, topic: str, *, increment: int = 1
    ) -> Memory:
        """Increment (or create) a weak-topic entry. Called on quiz/interview misses."""
        topic = topic.strip()
        result = await self.db.execute(
            select(Memory).where(
                Memory.workspace_id == workspace_id,
                Memory.kind == MemoryKind.weak_topic.value,
                Memory.topic == topic,
            )
        )
        memory = result.scalar_one_or_none()
        if memory is None:
            memory = Memory(
                workspace_id=workspace_id,
                kind=MemoryKind.weak_topic.value,
                topic=topic,
                content=f"Struggles with {topic}.",
                weight=increment,
            )
            self.db.add(memory)
        else:
            memory.weight += increment
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def add(
        self,
        workspace_id: uuid.UUID,
        *,
        kind: MemoryKind,
        content: str,
        topic: str | None = None,
    ) -> Memory:
        memory = Memory(
            workspace_id=workspace_id,
            kind=kind.value,
            topic=topic,
            content=content.strip(),
        )
        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)
        return memory

    async def list(
        self, workspace_id: uuid.UUID, *, kind: MemoryKind | None = None
    ) -> list[Memory]:
        stmt = select(Memory).where(Memory.workspace_id == workspace_id)
        if kind is not None:
            stmt = stmt.where(Memory.kind == kind.value)
        stmt = stmt.order_by(Memory.weight.desc(), Memory.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, memory_id: uuid.UUID) -> None:
        memory = await self.db.get(Memory, memory_id)
        if memory is not None:
            await self.db.delete(memory)
            await self.db.commit()

    async def search(
        self, workspace_id: uuid.UUID, query: str, *, limit: int = 5
    ) -> list[Memory]:
        """Keyword search over memory content/topic for the search_memory tool."""
        terms = [t for t in query.lower().split() if len(t) > 3][:6]
        if not terms:
            return []
        conditions = [Memory.content.ilike(f"%{t}%") for t in terms]
        conditions += [Memory.topic.ilike(f"%{t}%") for t in terms]
        stmt = (
            select(Memory)
            .where(Memory.workspace_id == workspace_id, or_(*conditions))
            .order_by(Memory.weight.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def planning_summary(
        self, workspace_id: uuid.UUID, *, max_weak: int = 5
    ) -> str:
        """A short summary injected into the planner prompt. Empty if nothing known."""
        memories = await self.list(workspace_id)
        if not memories:
            return ""

        weak = [m for m in memories if m.kind == MemoryKind.weak_topic.value][:max_weak]
        prefs = [m for m in memories if m.kind == MemoryKind.preference.value]

        parts: list[str] = []
        if weak:
            topics = ", ".join(f"{m.topic} (missed {m.weight}x)" for m in weak)
            parts.append(f"Weak topics to prioritize: {topics}.")
        if prefs:
            parts.append("Preferences: " + "; ".join(m.content for m in prefs) + ".")
        return " ".join(parts)
