"""Agent state and structured plan types.

The planner emits a `Plan` (validated), and the graph threads an `AgentState` through its
nodes. Keeping these in one place makes the agent's data flow easy to reason about.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TypedDict

from pydantic import BaseModel, Field

# The tools the planner may choose from.
TOOL_NAMES = [
    "search_notes",
    "search_web",
    "search_memory",
    "search_files",
]


class Plan(BaseModel):
    """The planner's decision for a single turn."""

    rewritten_query: str = Field(
        description="A retrieval-optimized rewrite of the user's question."
    )
    tools: list[str] = Field(
        default_factory=list,
        description="Which tools to use, from the allowed set.",
    )
    reasoning: str = Field(
        default="", description="One or two sentences on why these tools."
    )

    def normalized_tools(self) -> list[str]:
        return [t for t in self.tools if t in TOOL_NAMES]


@dataclass
class RetrievedChunk:
    document_id: uuid.UUID
    filename: str
    page: int | None
    content: str
    score: float


class AgentState(TypedDict, total=False):
    question: str
    workspace_id: str
    plan: Plan
    # Unified, numbered sources for citation: each is a dict with a "kind"
    # ("note" | "web") plus display fields. See graph.retrieve_node.
    sources: list[dict]
    context: str
    memory_summary: str
