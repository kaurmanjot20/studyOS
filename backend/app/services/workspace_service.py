"""Workspace business logic.

All workspace rules and persistence live here. Routers stay thin and call into this
service. Methods raise `WorkspaceNotFound` for missing records; the API layer maps that
to a 404.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import WorkspaceCreate, WorkspaceUpdate
from app.models.workspace import Workspace


class WorkspaceNotFound(Exception):
    """Raised when a workspace id does not exist."""

    def __init__(self, workspace_id: uuid.UUID) -> None:
        super().__init__(f"Workspace {workspace_id} not found")
        self.workspace_id = workspace_id


class WorkspaceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self) -> list[Workspace]:
        result = await self.db.execute(
            select(Workspace).order_by(Workspace.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, workspace_id: uuid.UUID) -> Workspace:
        workspace = await self.db.get(Workspace, workspace_id)
        if workspace is None:
            raise WorkspaceNotFound(workspace_id)
        return workspace

    async def create(self, data: WorkspaceCreate) -> Workspace:
        workspace = Workspace(
            name=data.name,
            description=data.description,
            subject=data.subject,
            color=data.color,
        )
        self.db.add(workspace)
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def update(
        self, workspace_id: uuid.UUID, data: WorkspaceUpdate
    ) -> Workspace:
        workspace = await self.get(workspace_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(workspace, field, value)
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def delete(self, workspace_id: uuid.UUID) -> None:
        workspace = await self.get(workspace_id)
        await self.db.delete(workspace)
        await self.db.commit()
