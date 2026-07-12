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
    RenameRequest,
    ResumeQuestionsRequest,
    ResumeReviewRequest,
    StudyArtifactRead,
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


@router.patch("/interview/{session_id}", response_model=InterviewSessionRead)
async def rename_interview(
    session_id: uuid.UUID,
    payload: RenameRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await InterviewService(db).rename(session_id, payload.title)
    except InterviewNotFound:
        raise HTTPException(status_code=404, detail="Interview session not found")


@router.delete("/interview/{session_id}", status_code=204)
async def delete_interview(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await InterviewService(db).delete(session_id)


@router.post(
    "/workspaces/{workspace_id}/resume/review", response_model=StudyArtifactRead
)
async def resume_review(
    workspace_id: uuid.UUID,
    payload: ResumeReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ResumeService(db).review(workspace_id, payload.document_id)
    except ResumeEmpty:
        raise HTTPException(status_code=400, detail="That document has no extractable text.")
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post(
    "/workspaces/{workspace_id}/resume/questions",
    response_model=StudyArtifactRead,
)
async def resume_questions(
    workspace_id: uuid.UUID,
    payload: ResumeQuestionsRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ResumeService(db).questions(
            workspace_id, payload.document_id, count=payload.count
        )
    except ResumeEmpty:
        raise HTTPException(status_code=400, detail="That document has no extractable text.")
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
