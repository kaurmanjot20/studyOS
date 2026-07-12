"""Study-artifact generation: quizzes, flashcards, and revision notes.

All three retrieve relevant context from the workspace (RAG) and generate grounded output
via the active LLM provider. Quiz scoring feeds wrong answers back into memory as weak
topics, so revision naturally prioritizes what the learner misses.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.service import MemoryService
from app.prompts.study import (
    FLASHCARDS_SYSTEM,
    QUIZ_SYSTEM,
    REVISION_SYSTEM,
    flashcards_user_prompt,
    quiz_user_prompt,
    revision_user_prompt,
)
from app.providers.base import ChatMessage, ProviderError
from app.providers.factory import build_provider
from app.rag.retrieval import assemble_context, retrieve
from app.services.provider_service import ProviderService
from app.utils.json_parse import extract_json


class StudyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.providers = ProviderService(db)

    async def _context(self, workspace_id: uuid.UUID, query: str, k: int = 8) -> str:
        """Retrieve grounding context for a subject; empty string if unavailable."""
        emb_config = await self.providers.resolve_embedding_config()
        if not emb_config.embedding_model:
            return ""
        try:
            embedder = build_provider(emb_config)
            chunks = await retrieve(
                self.db,
                embedder,
                workspace_id=workspace_id,
                query=query,
                embedding_model=emb_config.embedding_model,
                k=k,
            )
            return assemble_context(chunks)
        except Exception:
            return ""

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

    async def generate_quiz(
        self,
        workspace_id: uuid.UUID,
        *,
        subject: str,
        difficulty: str = "medium",
        count: int = 5,
    ) -> list[dict]:
        context = await self._context(workspace_id, subject or "interview prep")
        raw = await self._generate(
            QUIZ_SYSTEM, quiz_user_prompt(subject, difficulty, count, context)
        )
        try:
            data = extract_json(raw)
            questions = data["questions"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderError(f"Could not parse quiz output: {exc}")
        # Normalize / guard.
        clean: list[dict] = []
        for q in questions:
            if not isinstance(q, dict) or len(q.get("options", [])) < 2:
                continue
            clean.append(
                {
                    "topic": q.get("topic") or subject or "General",
                    "question": q["question"],
                    "options": q["options"],
                    "answer_index": int(q.get("answer_index", 0)),
                    "explanation": q.get("explanation", ""),
                }
            )
        return clean

    async def score_quiz(
        self, workspace_id: uuid.UUID, items: list[dict]
    ) -> dict:
        """Score submitted answers and record missed topics as weak topics.

        Each item: {topic, answer_index, selected_index}.
        """
        correct = 0
        missed_topics: list[str] = []
        for item in items:
            if item.get("selected_index") == item.get("answer_index"):
                correct += 1
            else:
                topic = (item.get("topic") or "").strip()
                if topic:
                    missed_topics.append(topic)

        memory = MemoryService(self.db)
        for topic in missed_topics:
            await memory.record_weak_topic(workspace_id, topic)

        total = len(items)
        return {
            "correct": correct,
            "total": total,
            "score_pct": round(100 * correct / total) if total else 0,
            "weak_topics_recorded": sorted(set(missed_topics)),
        }

    async def generate_flashcards(
        self, workspace_id: uuid.UUID, *, subject: str, count: int = 8
    ) -> list[dict]:
        context = await self._context(workspace_id, subject or "interview prep")
        raw = await self._generate(
            FLASHCARDS_SYSTEM, flashcards_user_prompt(subject, count, context)
        )
        try:
            cards = extract_json(raw)["cards"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderError(f"Could not parse flashcards output: {exc}")
        return [
            {"front": c["front"], "back": c["back"]}
            for c in cards
            if isinstance(c, dict) and c.get("front") and c.get("back")
        ]

    async def generate_revision(
        self, workspace_id: uuid.UUID, *, subject: str
    ) -> str:
        context = await self._context(workspace_id, subject or "interview prep")
        return await self._generate(
            REVISION_SYSTEM, revision_user_prompt(subject, context)
        )
