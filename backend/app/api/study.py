"""Study-artifact routes: quiz generation + scoring, flashcards, revision notes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.schemas import (
    FlashcardRequest,
    FlashcardsResponse,
    QuizRequest,
    QuizResponse,
    QuizScoreRequest,
    QuizScoreResult,
    RevisionRequest,
    RevisionResponse,
)
from app.providers.base import ProviderError
from app.services.study_service import StudyService

router = APIRouter(tags=["study"])


def get_service(db: AsyncSession = Depends(get_db)) -> StudyService:
    return StudyService(db)


@router.post("/workspaces/{workspace_id}/quiz", response_model=QuizResponse)
async def generate_quiz(
    workspace_id: uuid.UUID,
    payload: QuizRequest,
    service: StudyService = Depends(get_service),
):
    try:
        questions = await service.generate_quiz(
            workspace_id,
            subject=payload.subject,
            difficulty=payload.difficulty,
            count=payload.count,
        )
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return QuizResponse(questions=questions)


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


@router.post("/workspaces/{workspace_id}/flashcards", response_model=FlashcardsResponse)
async def generate_flashcards(
    workspace_id: uuid.UUID,
    payload: FlashcardRequest,
    service: StudyService = Depends(get_service),
):
    try:
        cards = await service.generate_flashcards(
            workspace_id, subject=payload.subject, count=payload.count
        )
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return FlashcardsResponse(cards=cards)


@router.post("/workspaces/{workspace_id}/revision", response_model=RevisionResponse)
async def generate_revision(
    workspace_id: uuid.UUID,
    payload: RevisionRequest,
    service: StudyService = Depends(get_service),
):
    try:
        markdown = await service.generate_revision(
            workspace_id, subject=payload.subject
        )
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return RevisionResponse(markdown=markdown)
