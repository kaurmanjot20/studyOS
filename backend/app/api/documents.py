"""Document routes (thin).

Upload accepts a multipart file, persists it, and schedules background processing so the
request returns immediately. The client polls document status to reflect progress.
"""

from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.schemas import DocumentRead
from app.rag.extraction import SUPPORTED_EXTENSIONS
from app.services.document_service import (
    DocumentNotFound,
    DocumentService,
    process_document,
)
from app.services.workspace_service import WorkspaceNotFound, WorkspaceService

router = APIRouter(tags=["documents"])


def get_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(db)


@router.post(
    "/workspaces/{workspace_id}/documents",
    response_model=DocumentRead,
    status_code=201,
)
async def upload_document(
    workspace_id: uuid.UUID,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # Workspace must exist.
    try:
        await WorkspaceService(db).get(workspace_id)
    except WorkspaceNotFound:
        raise HTTPException(status_code=404, detail="Workspace not found")

    ext = "." + (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_upload_mb} MB limit.",
        )

    service = DocumentService(db)
    doc = await service.create(workspace_id, file.filename or "upload", file.content_type, data)
    background.add_task(process_document, doc.id)
    return doc


@router.get("/workspaces/{workspace_id}/documents", response_model=list[DocumentRead])
async def list_documents(
    workspace_id: uuid.UUID, service: DocumentService = Depends(get_service)
):
    return await service.list(workspace_id)


@router.get("/documents/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID, service: DocumentService = Depends(get_service)
):
    try:
        return await service.get(document_id)
    except DocumentNotFound:
        raise HTTPException(status_code=404, detail="Document not found")


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID, service: DocumentService = Depends(get_service)
):
    try:
        await service.delete(document_id)
    except DocumentNotFound:
        raise HTTPException(status_code=404, detail="Document not found")
