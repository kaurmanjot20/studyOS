"""Chat routes: streaming planner-first RAG, plus session/history reads.

The POST endpoint streams Server-Sent Events in this order:
  event: plan     -> the planner's decision (tools + reasoning + rewritten query)
  event: sources  -> the retrieved chunks used as context (for citations)
  event: token    -> incremental answer tokens (many)
  event: error    -> a provider/setup problem (terminal)
  event: done     -> {session_id, message_id}

Planning + retrieval run inside the LangGraph agent; the answer is streamed from the
resolved provider. A dedicated DB session is used for the streaming work so it stays valid
for the whole response.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import AgentDeps, build_agent
from app.agents.state import RetrievedChunk
from app.db.session import SessionFactory, get_db
from app.models.schemas import ChatRequest, ChatSessionRead, MessageRead
from app.prompts.synthesis import SYNTHESIS_SYSTEM, synthesis_user_prompt
from app.providers.base import ChatMessage
from app.providers.factory import build_provider
from app.services.chat_service import ChatService
from app.services.provider_service import ProviderService
from app.services.workspace_service import WorkspaceNotFound, WorkspaceService

router = APIRouter(tags=["chat"])


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _source_dict(index: int, chunk: RetrievedChunk) -> dict:
    snippet = chunk.content.strip().replace("\n", " ")
    return {
        "index": index,
        "document_id": str(chunk.document_id),
        "filename": chunk.filename,
        "page": chunk.page,
        "score": chunk.score,
        "snippet": snippet[:240] + ("…" if len(snippet) > 240 else ""),
    }


async def _run_chat(workspace_id: uuid.UUID, payload: ChatRequest) -> AsyncIterator[str]:
    async with SessionFactory() as db:
        provider_service = ProviderService(db)
        config = await provider_service.resolve_active_config()
        # Wraps the active provider with a local fallback on rate limits (if enabled).
        provider = await provider_service.resolve_active_provider(config)
        # Embeddings may run on a different provider (e.g. local Ollama).
        emb_config = await provider_service.resolve_embedding_config()
        embedder = build_provider(emb_config)
        chat_service = ChatService(db)

        session = await chat_service.get_or_create_session(
            workspace_id, payload.session_id, title=payload.message[:60]
        )
        await chat_service.add_message(session.id, "user", payload.message)

        agent = build_agent(
            AgentDeps(
                db=db,
                provider=provider,
                chat_model=config.chat_model,
                embedding_model=emb_config.embedding_model,
                embedder=embedder,
            )
        )

        try:
            state = await agent.ainvoke(
                {"question": payload.message, "workspace_id": str(workspace_id)}
            )
        except Exception as exc:  # pragma: no cover - defensive
            yield _sse("error", {"detail": f"Planning failed: {exc}"})
            return

        plan = state["plan"]
        sources: list[RetrievedChunk] = state.get("sources", [])
        context: str = state.get("context", "")

        yield _sse(
            "plan",
            {
                "reasoning": plan.reasoning,
                "tools": plan.normalized_tools(),
                "rewritten_query": plan.rewritten_query,
            },
        )
        source_dicts = [_source_dict(i, s) for i, s in enumerate(sources, start=1)]
        yield _sse("sources", source_dicts)

        synthesis_messages = [
            ChatMessage(role="system", content=SYNTHESIS_SYSTEM),
            ChatMessage(
                role="user",
                content=synthesis_user_prompt(payload.message, context),
            ),
        ]

        answer_parts: list[str] = []
        try:
            async for chunk in provider.stream(
                synthesis_messages, model=config.chat_model
            ):
                if chunk.delta:
                    answer_parts.append(chunk.delta)
                    yield _sse("token", {"text": chunk.delta})

            # Some providers occasionally return an empty stream under load. Fall back
            # to a single blocking completion so the user still gets an answer.
            if not answer_parts:
                result = await provider.chat(
                    synthesis_messages, model=config.chat_model
                )
                if result.content:
                    answer_parts.append(result.content)
                    yield _sse("token", {"text": result.content})
        except Exception as exc:
            detail = str(exc)
            yield _sse(
                "error",
                {"detail": f"{detail[:300]} — check AI Provider Settings."},
            )
            if not answer_parts:
                return

        answer = "".join(answer_parts)
        message = await chat_service.add_message(
            session.id,
            "assistant",
            answer,
            sources=source_dicts,
            plan={
                "reasoning": plan.reasoning,
                "tools": plan.normalized_tools(),
                "rewritten_query": plan.rewritten_query,
            },
        )
        yield _sse(
            "done",
            {"session_id": str(session.id), "message_id": str(message.id)},
        )


@router.post("/workspaces/{workspace_id}/chat")
async def chat(
    workspace_id: uuid.UUID,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        await WorkspaceService(db).get(workspace_id)
    except WorkspaceNotFound:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return StreamingResponse(
        _run_chat(workspace_id, payload),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get(
    "/workspaces/{workspace_id}/chat/sessions",
    response_model=list[ChatSessionRead],
)
async def list_sessions(
    workspace_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    return await ChatService(db).list_sessions(workspace_id)


@router.get(
    "/chat/sessions/{session_id}/messages", response_model=list[MessageRead]
)
async def session_messages(
    session_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    return await ChatService(db).get_messages(session_id)
