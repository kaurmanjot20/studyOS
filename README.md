# StudyOS

An AI-powered interview-preparation workspace. It combines a user's own notes, books,
slides, PDFs, and resume with live web knowledge to prepare them for software-engineering
interviews.

It is **not** "chat with a PDF." Every request is routed by a **planner agent** that
decides which tools to use — search notes (RAG), search the web, read the resume, consult
memory of weak topics, generate a quiz, or write revision notes — before any answer is
produced. It is **provider-agnostic**: users bring their own LLM key (OpenAI, Anthropic,
Gemini, OpenRouter, or Ollama), and no vendor SDK is hardcoded into the app.

## Highlights

- **Planner-first agent** (LangGraph) with a visible plan trace
- **RAG** over your own documents with inline citations
- **Provider abstraction** — swap LLM providers with one setting, no code changes
- **Document pipeline** — PDF / DOCX / PPTX / TXT / images → extract → chunk → embed
- **Memory** of weak topics that shapes future revision and interviews
- **Mock interviews, quizzes, flashcards, revision notes**
- **MCP** integration (filesystem, Notion)

## Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js (App Router), Tailwind, shadcn/ui |
| Backend | FastAPI, Pydantic v2 |
| Database | PostgreSQL + pgvector |
| Agent | LangGraph |
| Parsing | PyMuPDF, python-docx, python-pptx, Tesseract (OCR) |
| Runtime | Docker Compose |

## Quick Start

```bash
cp .env.example .env        # then fill in secrets
docker compose up --build   # brings up db (postgres+pgvector), backend, frontend
```

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Open **Settings** in the app to configure your AI provider (bring your own API key) and
run **Test Connection**, then create a workspace and upload your notes to start.

## Project Status

Open-source and local-first (single user, no login required). Built in end-to-end phases:
authentication-free workspaces, a provider-agnostic LLM layer, a document pipeline, and a
planner-first RAG chat are in place, with mock interviews, study artifacts, web search,
and MCP arriving in subsequent phases.
