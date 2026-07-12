"""Study-artifact generation and history.

Generates quizzes, flashcards, and revision notes grounded in the workspace's documents,
and persists each generation as a `StudyArtifact` so every study tab has a browsable,
renamable history. Quiz scoring feeds wrong answers back into memory as weak topics.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.service import MemoryService
from app.models.study_artifact import StudyArtifact
from app.prompts.study import (
    FLASHCARDS_SYSTEM,
    QUIZ_SYSTEM,
    REVISION_SYSTEM,
    flashcards_user_prompt,
    quiz_user_prompt,
    revision_user_prompt,
)
from app.providers.base import ChatMessage, ProviderError
from app.services.context import build_context
from app.services.provider_service import ProviderService
from app.utils.json_parse import extract_json


class StudyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.providers = ProviderService(db)

    # --- generation helpers ---

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

    async def _save(
        self, workspace_id: uuid.UUID, kind: str, title: str, payload: dict
    ) -> StudyArtifact:
        artifact = StudyArtifact(
            workspace_id=workspace_id, kind=kind, title=title, payload=payload
        )
        self.db.add(artifact)
        await self.db.commit()
        await self.db.refresh(artifact)
        return artifact

    # --- artifact history CRUD ---

    async def list_artifacts(
        self, workspace_id: uuid.UUID, kind: str
    ) -> list[StudyArtifact]:
        result = await self.db.execute(
            select(StudyArtifact)
            .where(
                StudyArtifact.workspace_id == workspace_id,
                StudyArtifact.kind == kind,
            )
            .order_by(StudyArtifact.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_artifact(self, artifact_id: uuid.UUID) -> StudyArtifact | None:
        return await self.db.get(StudyArtifact, artifact_id)

    async def rename_artifact(
        self, artifact_id: uuid.UUID, title: str
    ) -> StudyArtifact | None:
        artifact = await self.db.get(StudyArtifact, artifact_id)
        if artifact is None:
            return None
        artifact.title = title.strip() or artifact.title
        await self.db.commit()
        await self.db.refresh(artifact)
        return artifact

    async def delete_artifact(self, artifact_id: uuid.UUID) -> None:
        artifact = await self.db.get(StudyArtifact, artifact_id)
        if artifact is not None:
            await self.db.delete(artifact)
            await self.db.commit()

    # --- generators (persist and return the saved artifact) ---

    async def generate_quiz(
        self,
        workspace_id: uuid.UUID,
        *,
        subject: str,
        difficulty: str = "medium",
        count: int = 5,
    ) -> StudyArtifact:
        context = await build_context(self.db, workspace_id, subject or "interview prep")
        raw = await self._generate(
            QUIZ_SYSTEM, quiz_user_prompt(subject, difficulty, count, context)
        )
        try:
            questions = extract_json(raw)["questions"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderError(f"Could not parse quiz output: {exc}")
        clean = [
            {
                "topic": q.get("topic") or subject or "General",
                "question": q["question"],
                "options": q["options"],
                "answer_index": int(q.get("answer_index", 0)),
                "explanation": q.get("explanation", ""),
            }
            for q in questions
            if isinstance(q, dict) and len(q.get("options", [])) >= 2
        ]
        title = f"{subject or 'Quiz'} · {difficulty}"
        return await self._save(workspace_id, "quiz", title, {"questions": clean})

    async def score_quiz(self, workspace_id: uuid.UUID, items: list[dict]) -> dict:
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
    ) -> StudyArtifact:
        context = await build_context(self.db, workspace_id, subject or "interview prep")
        raw = await self._generate(
            FLASHCARDS_SYSTEM, flashcards_user_prompt(subject, count, context)
        )
        try:
            cards = extract_json(raw)["cards"]
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderError(f"Could not parse flashcards output: {exc}")
        clean = [
            {"front": c["front"], "back": c["back"]}
            for c in cards
            if isinstance(c, dict) and c.get("front") and c.get("back")
        ]
        title = f"{subject or 'Flashcards'} · {len(clean)} cards"
        return await self._save(workspace_id, "flashcards", title, {"cards": clean})

    async def generate_revision(
        self, workspace_id: uuid.UUID, *, subject: str
    ) -> StudyArtifact:
        context = await build_context(self.db, workspace_id, subject or "interview prep")
        markdown = await self._generate(
            REVISION_SYSTEM, revision_user_prompt(subject, context)
        )
        title = subject or "Revision notes"
        return await self._save(workspace_id, "revision", title, {"markdown": markdown})
