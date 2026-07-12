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
