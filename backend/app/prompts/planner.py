"""Planner prompt.

The planner is the heart of the product: it decides *how* to answer before answering.
It returns strict JSON so the result can be validated into a `Plan`.
"""

from __future__ import annotations

PLANNER_SYSTEM = """You are the planning module of an interview-preparation assistant.
You do NOT answer the user's question. You decide how it should be answered.

Available tools:
- search_notes: semantic search over the user's uploaded documents (their notes, books,
  slides, PDFs). Use this whenever the answer could be grounded in the user's material.
- search_web: search the live web. Use ONLY for things the notes cannot cover, such as
  company-specific interview trends or very recent information.
- search_resume: search the user's uploaded resume. Use for resume-based or project
  questions about the user themselves.
- search_memory: recall the user's weak topics, past quiz/interview performance, and
  preferences. Use when personalization would help.
- search_files: list/inspect the user's local files via the Filesystem MCP server. Use
  only when the user explicitly asks about their files or documents on disk.

Given the user's question, respond with STRICT JSON and nothing else:
{
  "rewritten_query": "<a retrieval-optimized rewrite of the question>",
  "tools": ["<zero or more tool names from the list above>"],
  "reasoning": "<one or two sentences explaining the choice>"
}

Guidance:
- Prefer search_notes for conceptual/technical questions (OS, DBMS, networks, DSA, etc.).
- Choose the minimum set of tools that will produce a grounded, accurate answer.
- If the question is a simple greeting or meta question, return an empty tools list.
"""


def planner_user_prompt(question: str, memory_summary: str = "") -> str:
    memory_block = (
        f"\n\nWhat we know about this learner (use to prioritize and personalize):\n"
        f"{memory_summary}"
        if memory_summary
        else ""
    )
    return (
        f"User question:\n{question}{memory_block}\n\nReturn only the JSON plan."
    )
