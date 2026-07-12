"""Pydantic schemas (API contracts).

Kept separate from ORM models: these define what crosses the HTTP boundary. Services
accept and return these; routers never expose ORM objects directly.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    subject: str | None = Field(default=None, max_length=80)
    color: str | None = Field(default=None, max_length=24)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    subject: str | None = Field(default=None, max_length=80)
    color: str | None = Field(default=None, max_length=24)


class WorkspaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    subject: str | None
    color: str | None
    created_at: datetime
    updated_at: datetime


# --- Interview & Resume ---


class InterviewStartRequest(BaseModel):
    company: str = Field(default="", max_length=120)
    subject: str = Field(default="", max_length=160)
    difficulty: str = Field(default="medium")
    target_questions: int = Field(default=5, ge=1, le=12)


class InterviewAnswerRequest(BaseModel):
    answer: str = Field(min_length=1)


class InterviewSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    company: str | None
    subject: str | None
    difficulty: str
    status: str
    target_questions: int
    asked_count: int
    score: int | None
    summary: str | None
    transcript: list[dict]
    created_at: datetime
    updated_at: datetime


class ResumeReviewRequest(BaseModel):
    document_id: uuid.UUID


class ResumeReviewResponse(BaseModel):
    markdown: str


class ResumeQuestionsRequest(BaseModel):
    document_id: uuid.UUID
    count: int = Field(default=6, ge=1, le=15)


class ResumeQuestionsResponse(BaseModel):
    questions: list[str]


# --- Study artifacts ---


class QuizRequest(BaseModel):
    subject: str = Field(default="", max_length=200)
    difficulty: str = Field(default="medium")
    count: int = Field(default=5, ge=1, le=15)


class QuizQuestion(BaseModel):
    topic: str
    question: str
    options: list[str]
    answer_index: int
    explanation: str


class QuizResponse(BaseModel):
    questions: list[QuizQuestion]


class QuizScoreItem(BaseModel):
    topic: str
    answer_index: int
    selected_index: int | None = None


class QuizScoreRequest(BaseModel):
    items: list[QuizScoreItem]


class QuizScoreResult(BaseModel):
    correct: int
    total: int
    score_pct: int
    weak_topics_recorded: list[str]


class FlashcardRequest(BaseModel):
    subject: str = Field(default="", max_length=200)
    count: int = Field(default=8, ge=1, le=20)


class Flashcard(BaseModel):
    front: str
    back: str


class FlashcardsResponse(BaseModel):
    cards: list[Flashcard]


class RevisionRequest(BaseModel):
    subject: str = Field(default="", max_length=200)


class RevisionResponse(BaseModel):
    markdown: str


# --- Memory ---


class MemoryCreate(BaseModel):
    kind: str = Field(default="note")  # weak_topic | preference | note
    content: str = Field(min_length=1, max_length=2000)
    topic: str | None = Field(default=None, max_length=160)


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    kind: str
    topic: str | None
    content: str
    weight: int
    created_at: datetime
    updated_at: datetime


# --- Chat ---


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: uuid.UUID | None = None


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    sources: list | None
    plan: dict | None
    created_at: datetime


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


# --- Documents ---


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    filename: str
    content_type: str | None
    size_bytes: int
    status: str
    error: str | None
    title: str | None
    page_count: int | None
    word_count: int | None
    chunk_count: int
    embedding_model: str | None
    created_at: datetime
    updated_at: datetime


# --- Provider settings ---


class ProviderMetaRead(BaseModel):
    name: str
    label: str
    requires_api_key: bool
    supports_embeddings: bool
    default_base_url: str | None = None


class ProviderSettingsUpsert(BaseModel):
    provider: str = Field(min_length=1, max_length=32)
    # Omit to keep an existing key; empty string clears it.
    api_key: str | None = None
    chat_model: str | None = Field(default=None, max_length=120)
    embedding_model: str | None = Field(default=None, max_length=120)
    base_url: str | None = Field(default=None, max_length=300)
    set_active: bool = True


class ProviderSettingsRead(BaseModel):
    provider: str
    chat_model: str | None
    embedding_model: str | None
    base_url: str | None
    is_active: bool
    has_api_key: bool

    created_at: datetime
    updated_at: datetime


class ConnectionTestRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=32)
    api_key: str | None = None
    chat_model: str | None = None
    base_url: str | None = None


class ConnectionTestResult(BaseModel):
    ok: bool
    detail: str
    models_available: int | None = None


class ModelListResult(BaseModel):
    models: list[str]
