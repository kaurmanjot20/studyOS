"""Study-artifact routes: generation (persisted), history, and quiz scoring."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.schemas import (
    FlashcardRequest,
    QuizRequest,
    QuizScoreRequest,
    QuizScoreResult,
    RenameRequest,
    RevisionRequest,
    StudyArtifactRead,
    StudyArtifactSummary,
)
from app.providers.base import ProviderError
from app.services.study_service import StudyService

router = APIRouter(tags=["study"])


def get_service(db: AsyncSession = Depends(get_db)) -> StudyService:
    return StudyService(db)


@router.post("/workspaces/{workspace_id}/quiz", response_model=StudyArtifactRead)
async def generate_quiz(
    workspace_id: uuid.UUID,
    payload: QuizRequest,
    service: StudyService = Depends(get_service),
):
    try:
        return await service.generate_quiz(
            workspace_id,
            subject=payload.subject,
            difficulty=payload.difficulty,
            count=payload.count,
        )
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/workspaces/{workspace_id}/quiz/score", response_model=QuizScoreResult)
async def score_quiz(
    workspace_id: uuid.UUID,
    payload: QuizScoreRequest,
    service: StudyService = Depends(get_service),
):
    result = await service.score_quiz(
        workspace_id, [item.model_dump() for item in payload.items]
    )
    return QuizScoreResult(**result)


@router.post("/workspaces/{workspace_id}/flashcards", response_model=StudyArtifactRead)
async def generate_flashcards(
    workspace_id: uuid.UUID,
    payload: FlashcardRequest,
    service: StudyService = Depends(get_service),
):
    try:
        return await service.generate_flashcards(
            workspace_id, subject=payload.subject, count=payload.count
        )
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/workspaces/{workspace_id}/revision", response_model=StudyArtifactRead)
async def generate_revision(
    workspace_id: uuid.UUID,
    payload: RevisionRequest,
    service: StudyService = Depends(get_service),
):
    try:
        return await service.generate_revision(
            workspace_id, subject=payload.subject
        )
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# --- history ---


@router.get(
    "/workspaces/{workspace_id}/artifacts",
    response_model=list[StudyArtifactSummary],
)
async def list_artifacts(
    workspace_id: uuid.UUID,
    kind: str,
    service: StudyService = Depends(get_service),
):
    return await service.list_artifacts(workspace_id, kind)


@router.get("/artifacts/{artifact_id}", response_model=StudyArtifactRead)
async def get_artifact(
    artifact_id: uuid.UUID, service: StudyService = Depends(get_service)
):
    artifact = await service.get_artifact(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.patch("/artifacts/{artifact_id}", response_model=StudyArtifactRead)
async def rename_artifact(
    artifact_id: uuid.UUID,
    payload: RenameRequest,
    service: StudyService = Depends(get_service),
):
    artifact = await service.rename_artifact(artifact_id, payload.title)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.delete("/artifacts/{artifact_id}", status_code=204)
async def delete_artifact(
    artifact_id: uuid.UUID, service: StudyService = Depends(get_service)
):
    await service.delete_artifact(artifact_id)
