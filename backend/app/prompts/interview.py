"""Prompts for the mock-interview conductor and resume tools."""

from __future__ import annotations

QUESTION_SYSTEM = """You are a senior technical interviewer conducting a mock interview.
Ask ONE question at a time, appropriate to the target company, subject, and difficulty.
Build on the conversation; do not repeat earlier questions. Prefer questions that probe
real understanding. Respond with STRICT JSON only:
{ "question": "<the question>", "topic": "<the concept being tested>" }
"""


def question_user_prompt(
    company: str, subject: str, difficulty: str, asked: list[str], context: str
) -> str:
    prev = "\n".join(f"- {q}" for q in asked) if asked else "(none yet)"
    ctx = f"\n\nCandidate's notes for grounding:\n{context}\n" if context.strip() else ""
    return (
        f"Company: {company or 'a top software company'}\n"
        f"Subject: {subject or 'general software-engineering'}\n"
        f"Difficulty: {difficulty}\n"
        f"Questions already asked:\n{prev}{ctx}\n"
        "Return the next question as JSON."
    )


EVAL_SYSTEM = """You evaluate a candidate's answer to an interview question. Be fair but
honest, like a real interviewer. Respond with STRICT JSON only:
{
  "score": <integer 0-10>,
  "feedback": "<2-3 sentences: what was good, what was missing or wrong>",
  "topic": "<the concept, for tracking weak areas>"
}
A score of 6 or less means the candidate struggled with this topic.
"""


def eval_user_prompt(question: str, topic: str, answer: str) -> str:
    return (
        f"Question: {question}\n"
        f"Topic: {topic}\n"
        f"Candidate's answer: {answer}\n\n"
        "Return the evaluation as JSON."
    )


SUMMARY_SYSTEM = """You are summarizing a completed mock interview for the candidate.
Given the transcript (questions, answers, per-answer scores), write concise Markdown
feedback: overall impression, clear strengths, and specific areas to improve. Be
constructive and actionable.
"""


def summary_user_prompt(transcript: list[dict], score_pct: int) -> str:
    lines = []
    for i, t in enumerate(transcript, 1):
        lines.append(
            f"Q{i} ({t.get('topic')}): {t.get('question')}\n"
            f"  Answer: {t.get('answer', '(skipped)')}\n"
            f"  Score: {t.get('score', 0)}/10 — {t.get('feedback', '')}"
        )
    body = "\n".join(lines)
    return (
        f"Overall score: {score_pct}%.\n\nTranscript:\n{body}\n\n"
        "Write the feedback in Markdown."
    )


# --- Resume ---

RESUME_REVIEW_SYSTEM = """You are a technical recruiter and engineering manager reviewing
a candidate's resume for software-engineering roles. Write concise Markdown with:
**Strengths**, **Weaknesses / red flags**, and **Concrete improvements** (bullet points,
specific and actionable). Be honest and useful.
"""


def resume_review_user_prompt(resume_text: str) -> str:
    return f"Resume:\n{resume_text}\n\nWrite the review in Markdown."


RESUME_QUESTIONS_SYSTEM = """You are an interviewer preparing to grill a candidate on
THEIR resume. Based on the resume, produce project- and experience-based questions plus
likely follow-ups. Respond with STRICT JSON only:
{ "questions": ["<question>", "<question>"] }
Focus on their actual projects, technologies, and claims.
"""


def resume_questions_user_prompt(resume_text: str, count: int) -> str:
    return (
        f"Resume:\n{resume_text}\n\n"
        f"Generate {count} resume-specific interview questions. Return only the JSON."
    )
