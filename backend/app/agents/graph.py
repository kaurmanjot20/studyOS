"""The planner-first agent graph (LangGraph).

Flow:  planner → retrieve → (END)

The planner decides which tools to use; the retrieve node executes them (only
`search_notes` is wired in Phase 4). The final answer is *streamed* by the chat endpoint
using the resolved provider, so token streaming stays outside the graph while planning and
retrieval — the parts that must complete before generation — run inside it.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState, Plan
from app.memory.service import MemoryService
from app.prompts.planner import PLANNER_SYSTEM, planner_user_prompt
from app.providers.base import ChatMessage, LLMProvider
from app.rag.retrieval import assemble_context, retrieve


@dataclass
class AgentDeps:
    db: AsyncSession
    provider: LLMProvider
    chat_model: str
    embedding_model: str | None
    # Provider used to embed the query for retrieval (may differ from the chat provider).
    embedder: LLMProvider | None = None


def _parse_plan(text: str, question: str) -> Plan:
    """Parse the planner's JSON, tolerating code fences and surrounding prose."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned).rstrip("`").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start : end + 1]
    try:
        data = json.loads(cleaned)
        plan = Plan(**data)
        if not plan.rewritten_query:
            plan.rewritten_query = question
        return plan
    except (json.JSONDecodeError, TypeError, ValueError):
        # Safe fallback: search the notes with the raw question.
        return Plan(
            rewritten_query=question,
            tools=["search_notes"],
            reasoning="Fell back to note search (planner output was unparseable).",
        )


def _make_planner(deps: AgentDeps):
    async def planner(state: AgentState) -> dict:
        question = state["question"]
        workspace_id = uuid.UUID(state["workspace_id"])
        # The planner consults memory before deciding how to answer.
        memory_summary = await MemoryService(deps.db).planning_summary(workspace_id)
        try:
            result = await deps.provider.chat(
                [
                    ChatMessage(role="system", content=PLANNER_SYSTEM),
                    ChatMessage(
                        role="user",
                        content=planner_user_prompt(question, memory_summary),
                    ),
                ],
                model=deps.chat_model,
                temperature=0,
            )
            plan = _parse_plan(result.content, question)
        except Exception:
            plan = Plan(
                rewritten_query=question,
                tools=["search_notes"],
                reasoning="Planner unavailable; defaulted to note search.",
            )
        return {"plan": plan, "memory_summary": memory_summary}

    return planner


def _make_retrieve(deps: AgentDeps):
    async def retrieve_node(state: AgentState) -> dict:
        plan: Plan = state["plan"]
        tools = plan.normalized_tools()
        workspace_id = uuid.UUID(state["workspace_id"])
        sources = []
        embedder = deps.embedder or deps.provider

        # search_notes (RAG) and search_memory are wired; search_web/search_resume
        # are recognised by the planner and implemented in their own phases.
        if "search_notes" in tools and deps.embedding_model:
            try:
                sources = await retrieve(
                    deps.db,
                    embedder,
                    workspace_id=workspace_id,
                    query=plan.rewritten_query,
                    embedding_model=deps.embedding_model,
                )
            except Exception:
                # Retrieval failure (e.g. embeddings unavailable) shouldn't abort the
                # turn — degrade to an ungrounded answer rather than erroring out.
                sources = []

        context = assemble_context(sources)

        # The learner profile (weak topics + preferences) always informs the answer.
        memory_summary = state.get("memory_summary", "")
        if memory_summary:
            context = (f"Learner profile: {memory_summary}\n\n" + context).strip()

        # search_memory additionally pulls specific relevant memories into context.
        if "search_memory" in tools:
            memories = await MemoryService(deps.db).search(
                workspace_id, plan.rewritten_query
            )
            if memories:
                lines = "\n".join(f"- {m.content}" for m in memories)
                context = (context + f"\n\nKnown about the learner:\n{lines}").strip()

        return {"sources": sources, "context": context}

    return retrieve_node


def build_agent(deps: AgentDeps):
    graph = StateGraph(AgentState)
    graph.add_node("planner", _make_planner(deps))
    graph.add_node("retrieve", _make_retrieve(deps))
    graph.set_entry_point("planner")
    graph.add_edge("planner", "retrieve")
    graph.add_edge("retrieve", END)
    return graph.compile()
