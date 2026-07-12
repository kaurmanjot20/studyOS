"""Prompts for generated study artifacts: quizzes, flashcards, revision notes.

Each asks for strict JSON (except revision, which is Markdown) so results parse reliably.
When context from the user's documents is available it is used; otherwise the model draws
on general knowledge for the subject.
"""

from __future__ import annotations

QUIZ_SYSTEM = """You are an examiner creating interview-prep quiz questions for software
-engineering subjects (OS, DBMS, networks, OOP, system design, DSA, languages).

Generate multiple-choice questions. Respond with STRICT JSON only:
{
  "questions": [
    {
      "topic": "<the specific concept, e.g. 'Deadlocks'>",
      "question": "<the question>",
      "options": ["<A>", "<B>", "<C>", "<D>"],
      "answer_index": <0-3, the correct option>,
      "explanation": "<why the answer is correct, 1-2 sentences>"
    }
  ]
}

Rules:
- Exactly 4 options per question; exactly one correct.
- No duplicate questions; vary the concepts tested.
- Match the requested difficulty. Ground questions in the provided context when given.
- Set "topic" precisely — it is used to track the learner's weak areas.
"""


def quiz_user_prompt(subject: str, difficulty: str, count: int, context: str) -> str:
    ctx = f"\n\nContext from the learner's notes:\n{context}\n" if context.strip() else ""
    return (
        f"Subject/topic: {subject or 'general software-engineering interview prep'}\n"
        f"Difficulty: {difficulty}\n"
        f"Number of questions: {count}{ctx}\n"
        "Return only the JSON."
    )


FLASHCARDS_SYSTEM = """You create concise interview-prep flashcards. Respond with STRICT
JSON only:
{
  "cards": [
    { "front": "<a question or term>", "back": "<a tight, correct answer>" }
  ]
}
Keep backs short and memorizable. Ground cards in the provided context when given.
"""


def flashcards_user_prompt(subject: str, count: int, context: str) -> str:
    ctx = f"\n\nContext from the learner's notes:\n{context}\n" if context.strip() else ""
    return (
        f"Subject/topic: {subject or 'software-engineering interview prep'}\n"
        f"Number of cards: {count}{ctx}\n"
        "Return only the JSON."
    )


REVISION_SYSTEM = """You write last-minute revision notes: a single-page, high-density
cheat sheet for a software-engineering interview. Use Markdown with short sections,
bullet points, and key definitions. Be accurate and concise. Ground it in the provided
context when given; otherwise use general knowledge for the subject.
"""


def revision_user_prompt(subject: str, context: str) -> str:
    ctx = f"\n\nContext from the learner's notes:\n{context}\n" if context.strip() else ""
    return (
        f"Subject/topic: {subject or 'software-engineering interview prep'}{ctx}\n"
        "Write the one-page revision sheet in Markdown."
    )
