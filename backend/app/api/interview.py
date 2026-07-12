"""Interview + resume routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.schemas import (
    InterviewAnswerRequest,
    InterviewSessionRead,
    InterviewStartRequest,
    ResumeQuestionsRequest,
    ResumeQuestionsResponse,
    ResumeReviewRequest,
    ResumeReviewResponse,
)
from app.providers.base import ProviderError
from app.services.interview_service import InterviewNotFound, InterviewService
from app.services.resume_service import ResumeEmpty, ResumeService

router = APIRouter(tags=["interview"])


@router.post(
    "/workspaces/{workspace_id}/interview/start", response_model=InterviewSessionRead
)
async def start_interview(
    workspace_id: uuid.UUID,
    payload: InterviewStartRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await InterviewService(db).start(
            workspace_id,
            company=payload.company,
            subject=payload.subject,
            difficulty=payload.difficulty,
            target_questions=payload.target_questions,
        )
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post(
    "/interview/{session_id}/answer", response_model=InterviewSessionRead
)
async def answer_interview(
    session_id: uuid.UUID,
    payload: InterviewAnswerRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await InterviewService(db).answer(session_id, payload.answer)
    except InterviewNotFound:
        raise HTTPException(status_code=404, detail="Interview session not found")
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get(
    "/workspaces/{workspace_id}/interview/sessions",
    response_model=list[InterviewSessionRead],
)
async def list_interviews(
    workspace_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    return await InterviewService(db).list_sessions(workspace_id)


@router.get("/interview/{session_id}", response_model=InterviewSessionRead)
async def get_interview(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await InterviewService(db).get(session_id)
    except InterviewNotFound:
        raise HTTPException(status_code=404, detail="Interview session not found")


@router.post(
    "/workspaces/{workspace_id}/resume/review", response_model=ResumeReviewResponse
)
async def resume_review(
    workspace_id: uuid.UUID,
    payload: ResumeReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        markdown = await ResumeService(db).review(payload.document_id)
    except ResumeEmpty:
        raise HTTPException(status_code=400, detail="That document has no extractable text.")
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return ResumeReviewResponse(markdown=markdown)


@router.post(
    "/workspaces/{workspace_id}/resume/questions",
    response_model=ResumeQuestionsResponse,
)
async def resume_questions(
    workspace_id: uuid.UUID,
    payload: ResumeQuestionsRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        questions = await ResumeService(db).questions(
            payload.document_id, count=payload.count
        )
    except ResumeEmpty:
        raise HTTPException(status_code=400, detail="That document has no extractable text.")
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return ResumeQuestionsResponse(questions=questions)
