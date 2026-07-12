"""Memory routes (thin): list, add, and delete long-term memory entries."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.memory.service import MemoryService
from app.models.memory import MemoryKind
from app.models.schemas import MemoryCreate, MemoryRead

router = APIRouter(tags=["memory"])


def get_service(db: AsyncSession = Depends(get_db)) -> MemoryService:
    return MemoryService(db)


@router.get("/workspaces/{workspace_id}/memory", response_model=list[MemoryRead])
async def list_memory(
    workspace_id: uuid.UUID, service: MemoryService = Depends(get_service)
):
    return await service.list(workspace_id)


@router.post("/workspaces/{workspace_id}/memory", response_model=MemoryRead, status_code=201)
async def add_memory(
    workspace_id: uuid.UUID,
    payload: MemoryCreate,
    service: MemoryService = Depends(get_service),
):
    try:
        kind = MemoryKind(payload.kind)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid kind: {payload.kind}")
    if kind == MemoryKind.weak_topic and payload.topic:
        return await service.record_weak_topic(workspace_id, payload.topic)
    return await service.add(
        workspace_id, kind=kind, content=payload.content, topic=payload.topic
    )


@router.delete("/memory/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: uuid.UUID, service: MemoryService = Depends(get_service)
):
    await service.delete(memory_id)
