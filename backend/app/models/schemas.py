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
