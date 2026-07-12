"""Resume tools: review a resume and generate resume-specific interview questions.

The resume is an ordinary uploaded document; its text is reassembled from stored chunks.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Chunk
from app.prompts.interview import (
    RESUME_QUESTIONS_SYSTEM,
    RESUME_REVIEW_SYSTEM,
    resume_questions_user_prompt,
    resume_review_user_prompt,
)
from app.providers.base import ChatMessage, ProviderError
from app.services.provider_service import ProviderService
from app.utils.json_parse import extract_json


class ResumeEmpty(Exception):
    pass


class ResumeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.providers = ProviderService(db)

    async def _document_text(self, document_id: uuid.UUID) -> str:
        result = await self.db.execute(
            select(Chunk.content)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.ordinal)
        )
        parts = [row[0] for row in result.all()]
        text = "\n".join(parts).strip()
        if not text:
            raise ResumeEmpty()
        return text[:8000]  # keep within a reasonable prompt budget

    async def _generate(self, system: str, user: str) -> str:
        config = await self.providers.resolve_active_config()
        provider = await self.providers.resolve_active_provider(config)
        result = await provider.chat(
            [
                ChatMessage(role="system", content=system),
                ChatMessage(role="user", content=user),
            ],
            model=config.chat_model,
            temperature=0.4,
        )
        return result.content

    async def review(self, document_id: uuid.UUID) -> str:
        text = await self._document_text(document_id)
        return await self._generate(RESUME_REVIEW_SYSTEM, resume_review_user_prompt(text))

    async def questions(self, document_id: uuid.UUID, *, count: int = 6) -> list[str]:
        text = await self._document_text(document_id)
        raw = await self._generate(
            RESUME_QUESTIONS_SYSTEM, resume_questions_user_prompt(text, count)
        )
        try:
            return [q for q in extract_json(raw)["questions"] if isinstance(q, str)]
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderError(f"Could not parse resume questions: {exc}")
