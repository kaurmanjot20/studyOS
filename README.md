# StudyOS

An AI-powered interview-preparation workspace. It combines your own notes, books, slides,
PDFs, and resume with live web knowledge to prepare you for software-engineering
interviews.

It is **not** "chat with a PDF." Every request is routed by a **planner agent** that
decides which tools to use — search notes (RAG), search the web, consult memory of weak
topics, or inspect your files over MCP — *before* any answer is produced. It is
**provider-agnostic**: bring your own LLM key (OpenAI, Anthropic, Gemini, OpenRouter,
NVIDIA, or local Ollama), with an automatic local fallback when a hosted tier rate-limits.

> Open-source, local-first, single-user — no login required.

---

## Highlights

- **Planner-first agent** (LangGraph) with a visible plan trace in the UI
- **RAG** over your own documents with inline, clickable citations
- **Provider abstraction** — swap LLM providers with one setting, no code changes; local
  fallback (Ollama) kicks in automatically on rate limits
- **Document pipeline** — PDF / DOCX / PPTX / TXT / images (OCR) → extract → chunk → embed
- **Memory** of weak topics that shapes future revision and interviews
- **Mock interviews** (scored, with feedback + history) and **resume** review / Q&A
- **Quizzes, flashcards, revision** cheat sheets — quiz misses feed back into memory
- **Web search** when your notes are insufficient, clearly labeled vs note sources
- **MCP** integration (Filesystem + Notion), extensible registry, exposed to the planner

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js (App Router), Tailwind, shadcn/ui, dark-first |
| Backend | FastAPI, Pydantic v2, async SQLAlchemy |
| Database | PostgreSQL + pgvector (HNSW cosine index) |
| Agent | LangGraph |
| Parsing | PyMuPDF, python-docx, python-pptx, Tesseract (OCR) |
| Integrations | MCP (Model Context Protocol), DuckDuckGo web search |
| Runtime | Docker Compose |

---

## Architecture

```
                         ┌──────────────────────────────────────────┐
                         │   Frontend — Next.js · Tailwind · shadcn  │
                         │   3-pane shell · streaming chat · settings│
                         └───────────────┬──────────────────────────┘
                                         │ HTTPS / SSE
                         ┌───────────────▼──────────────────────────┐
                         │            Backend — FastAPI              │
                         │  api/     thin routes → services          │
                         │  agents/  LangGraph planner + tool nodes  │
                         │  rag/     rewrite · retrieve · assemble    │
                         │  providers/  LLMProvider + adapters + fallback │
                         │  memory/ services/ prompts/ …             │
                         └───────┬───────────────────────┬───────────┘
                                 │                        │
                    ┌────────────▼─────────┐   ┌──────────▼───────────┐
                    │ Postgres + pgvector  │   │ Providers · Web · MCP│
                    └──────────────────────┘   └──────────────────────┘
```

**Planner-first flow.** Every turn runs a LangGraph graph: `planner → retrieve → (stream)`.
The planner emits a structured plan (which tools + why), the retrieve node executes the
chosen tools (notes RAG, web search, memory, filesystem MCP), and the answer is streamed
from the resolved provider with citations. The plan and sources are surfaced live in the
right sidebar.

**Provider abstraction.** All model access goes through `LLMProvider` (`chat`, `stream`,
`embed`, `test_connection`, `list_models`). Adapters for OpenAI, Anthropic, Gemini,
OpenRouter, NVIDIA (OpenAI-compatible via httpx — no vendor SDKs) and Ollama. A
`FallbackProvider` transparently retries on a local Ollama model when the primary is
rate-limited. Embeddings can use a **separate** provider from chat (e.g. chat on
OpenRouter, embeddings on local Ollama).

**The learning loop.** Quiz and mock-interview misses are recorded as *weak topics* in
memory; the planner consults memory before answering, so chat and revision automatically
prioritize what you struggle with.

---

## Folder Guide

```
backend/app/
  api/         FastAPI routers (thin): chat, documents, settings, study, interview, mcp…
  agents/      LangGraph graph, planner, agent state
  rag/         extraction, chunking, retrieval
  providers/   LLMProvider interface + adapters + factory + fallback  (only vendor calls)
  memory/      long-term memory service
  services/    business logic (document, chat, study, interview, resume, web_search, mcp…)
  models/      SQLAlchemy models + Pydantic schemas
  db/          async engine, session, migration wiring
  prompts/     planner / synthesis / study / interview prompt templates
  core/        config, security (key encryption)
  alembic/     migrations
frontend/
  app/         App Router entry + global styles
  components/  shell (3-pane), chat, study, interview, settings, documents
  lib/         api client, SSE chat stream, types
```

---

## Quick Start (Docker)

```bash
cp .env.example .env        # then fill in secrets (or leave defaults for local dev)
docker compose up --build   # db (postgres+pgvector) + backend + frontend
```

- **App:** http://localhost:3000
- **API docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

Open **Settings** (gear, top-right) to pick your AI provider, paste your own API key, run
**Test Connection**, then create a workspace and upload notes.

> After editing `.env`, run `docker compose up -d backend` to reload it (a plain
> `restart` will not pick up new env values).

---

## Environment Setup

Key `.env` values (see `.env.example` for the full list):

| Variable | Purpose |
|----------|---------|
| `DEFAULT_LLM_PROVIDER` / `DEFAULT_LLM_MODEL` | dev fallback provider + chat model |
| `EMBEDDING_PROVIDER` / `DEFAULT_EMBEDDING_MODEL` / `EMBEDDING_DIM` | embeddings (must match model's dimension; changing `EMBEDDING_DIM` needs `docker compose down -v`) |
| `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `NVIDIA_API_KEY` | provider keys (or set them in Settings) |
| `ENABLE_LOCAL_FALLBACK`, `FALLBACK_MODEL` | local Ollama fallback on rate limits |
| `ENCRYPTION_KEY` | encrypts stored provider keys at rest |
| `MCP_FILESYSTEM_ENABLED`, `NOTION_API_KEY` | MCP servers |

**Local models (recommended for unlimited, key-free use):** install
[Ollama](https://ollama.com/download), then `ollama pull llama3.2` (chat) and
`ollama pull nomic-embed-text` (embeddings). The backend reaches host Ollama via
`host.docker.internal`.

---

## Local Development

- **Backend:** code is bind-mounted; `uvicorn --reload` picks up changes. Migrations run
  on container start via `entrypoint.sh`; run one manually with
  `docker compose exec backend alembic upgrade head`.
- **Frontend:** `next dev` runs in its container with hot reload. To develop bare:
  `cd frontend && npm install && npm run dev` (but don't run it alongside the Docker
  frontend — they'll both want port 3000).
- **New migration:** `docker compose exec backend alembic revision -m "msg"`.
- **Logs:** `docker compose logs -f`.

---

## Roadmap

- Multi-user hosting (optional auth layer — intentionally out of scope today)
- Streaming for study/interview generation
- Richer MCP server catalog + per-workspace MCP config
- Spaced-repetition scheduling for flashcards
- Interview audio (speech-to-text answers)
- Export revision sheets to PDF / Notion

---

## Project Status

Built end-to-end in phases: workspaces, provider abstraction + fallback, document
pipeline, planner-first RAG chat, memory, quizzes/flashcards/revision, mock interviews +
resume, web search, MCP, and OCR — each verified against real infrastructure.
