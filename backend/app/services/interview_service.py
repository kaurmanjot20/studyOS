"""Mock interview conductor.

Runs a turn-based interview: generate a question → the candidate answers → evaluate and
track weak areas → next question → final feedback. Low-scoring topics are recorded to
memory so revision and future planning prioritize them.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.service import MemoryService
from app.models.interview import InterviewSession
from app.prompts.interview import (
    EVAL_SYSTEM,
    QUESTION_SYSTEM,
    SUMMARY_SYSTEM,
    eval_user_prompt,
    question_user_prompt,
    summary_user_prompt,
)
from app.providers.base import ChatMessage, ProviderError
from app.services.context import build_context
from app.services.provider_service import ProviderService
from app.utils.json_parse import extract_json

_WEAK_THRESHOLD = 6


class InterviewNotFound(Exception):
    pass


class InterviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.providers = ProviderService(db)

    async def _generate(self, system: str, user: str, *, temperature: float = 0.5) -> str:
        config = await self.providers.resolve_active_config()
        provider = await self.providers.resolve_active_provider(config)
        result = await provider.chat(
            [
                ChatMessage(role="system", content=system),
                ChatMessage(role="user", content=user),
            ],
            model=config.chat_model,
            temperature=temperature,
        )
        return result.content

    async def _next_question(self, session: InterviewSession) -> dict:
        context = await build_context(
            self.db, session.workspace_id, session.subject or "interview", k=4
        )
        asked = [t["question"] for t in session.transcript]
        raw = await self._generate(
            QUESTION_SYSTEM,
            question_user_prompt(
                session.company or "",
                session.subject or "",
                session.difficulty,
                asked,
                context,
            ),
        )
        try:
            data = extract_json(raw)
            return {"question": data["question"], "topic": data.get("topic", session.subject or "General")}
        except (ValueError, KeyError, TypeError):
            return {
                "question": raw.strip()[:400] or "Tell me about a challenging bug you fixed.",
                "topic": session.subject or "General",
            }

    async def start(
        self,
        workspace_id: uuid.UUID,
        *,
        company: str,
        subject: str,
        difficulty: str,
        target_questions: int,
    ) -> InterviewSession:
        label = " · ".join(p for p in [company, subject] if p) or "Interview"
        session = InterviewSession(
            workspace_id=workspace_id,
            title=label,
            company=company or None,
            subject=subject or None,
            difficulty=difficulty,
            target_questions=target_questions,
            transcript=[],
        )
        q = await self._next_question(session)
        session.transcript = [q]
        session.asked_count = 1
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def answer(self, session_id: uuid.UUID, answer: str) -> InterviewSession:
        session = await self.db.get(InterviewSession, session_id)
        if session is None:
            raise InterviewNotFound()
        if session.status == "completed" or not session.transcript:
            return session

        # Rebuild the transcript with fresh dicts so the JSONB change is always
        # detected (SQLAlchemy does not track in-place mutation of JSON columns).
        transcript = [dict(t) for t in session.transcript]
        current = transcript[-1]
        raw = await self._generate(
            EVAL_SYSTEM,
            eval_user_prompt(current["question"], current.get("topic", ""), answer),
            temperature=0.2,
        )
        try:
            ev = extract_json(raw)
            score = max(0, min(10, int(ev.get("score", 5))))
            feedback = ev.get("feedback", "")
            topic = ev.get("topic") or current.get("topic") or "General"
        except (ValueError, KeyError, TypeError):
            score, feedback, topic = 5, raw.strip()[:300], current.get("topic", "General")

        transcript[-1] = {
            **current,
            "answer": answer,
            "score": score,
            "feedback": feedback,
            "topic": topic,
        }
        session.transcript = transcript

        if score <= _WEAK_THRESHOLD:
            await MemoryService(self.db).record_weak_topic(session.workspace_id, topic)

        if session.asked_count >= session.target_questions:
            await self._finish(session)
        else:
            nxt = await self._next_question(session)
            session.transcript = transcript + [nxt]
            session.asked_count += 1

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def _finish(self, session: InterviewSession) -> None:
        scored = [t for t in session.transcript if "score" in t]
        avg10 = sum(t["score"] for t in scored) / len(scored) if scored else 0
        score_pct = round(avg10 * 10)
        summary = await self._generate(
            SUMMARY_SYSTEM, summary_user_prompt(session.transcript, score_pct), temperature=0.4
        )
        session.status = "completed"
        session.score = score_pct
        session.summary = summary

    async def list_sessions(self, workspace_id: uuid.UUID) -> list[InterviewSession]:
        result = await self.db.execute(
            select(InterviewSession)
            .where(InterviewSession.workspace_id == workspace_id)
            .order_by(InterviewSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, session_id: uuid.UUID) -> InterviewSession:
        session = await self.db.get(InterviewSession, session_id)
        if session is None:
            raise InterviewNotFound()
        return session

    async def rename(self, session_id: uuid.UUID, title: str) -> InterviewSession:
        session = await self.get(session_id)
        session.title = title.strip() or session.title
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def delete(self, session_id: uuid.UUID) -> None:
        session = await self.db.get(InterviewSession, session_id)
        if session is not None:
            await self.db.delete(session)
            await self.db.commit()
