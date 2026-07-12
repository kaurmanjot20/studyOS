"""Workspace routes (thin).

Validate input, delegate to `WorkspaceService`, shape the response. No business logic
here.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.schemas import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate
from app.services.workspace_service import WorkspaceNotFound, WorkspaceService

router = APIRouter(tags=["workspaces"])


def get_service(db: AsyncSession = Depends(get_db)) -> WorkspaceService:
    return WorkspaceService(db)


@router.get("", response_model=list[WorkspaceRead])
async def list_workspaces(service: WorkspaceService = Depends(get_service)):
    return await service.list()


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate, service: WorkspaceService = Depends(get_service)
):
    return await service.create(payload)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: uuid.UUID, service: WorkspaceService = Depends(get_service)
):
    try:
        return await service.get(workspace_id)
    except WorkspaceNotFound:
        raise HTTPException(status_code=404, detail="Workspace not found")


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    workspace_id: uuid.UUID,
    payload: WorkspaceUpdate,
    service: WorkspaceService = Depends(get_service),
):
    try:
        return await service.update(workspace_id, payload)
    except WorkspaceNotFound:
        raise HTTPException(status_code=404, detail="Workspace not found")


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: uuid.UUID, service: WorkspaceService = Depends(get_service)
):
    try:
        await service.delete(workspace_id)
    except WorkspaceNotFound:
        raise HTTPException(status_code=404, detail="Workspace not found")
