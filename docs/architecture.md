# InterviewOS — Architecture

> An AI interview-preparation workspace. The system is **planner-first**: every user
> turn is routed by an agent that decides which tools (notes RAG, web, resume, memory,
> quiz, revision) are needed before any answer is produced. It is **provider-agnostic**:
> users bring their own LLM key, and no vendor SDK leaks outside the provider layer.

---

## 1. System Overview

```
                         ┌──────────────────────────────────────────┐
                         │                Frontend                   │
                         │  Next.js (App Router) · Tailwind · shadcn │
                         │  3-pane shell · streaming chat · settings │
                         └───────────────┬──────────────────────────┘
                                         │ HTTPS / SSE
                         ┌───────────────▼──────────────────────────┐
                         │                Backend (FastAPI)          │
                         │                                           │
                         │  api/         thin routes → services      │
                         │  services/    business logic              │
                         │  agents/      LangGraph planner + tools   │
                         │  rag/         rewrite · retrieve · assemble│
                         │  providers/   LLMProvider + 5 adapters    │
                         │  memory/      weak topics · history       │
                         │  db/ models/  SQLAlchemy · Alembic        │
                         └───────┬───────────────────────┬───────────┘
                                 │                        │
                    ┌────────────▼─────────┐   ┌──────────▼───────────┐
                    │ Postgres + pgvector  │   │  External (per user) │
                    │ users · workspaces   │   │  OpenAI / Anthropic  │
                    │ documents · chunks   │   │  Gemini / OpenRouter │
                    │ messages · memories  │   │  Ollama · Web · MCP  │
                    └──────────────────────┘   └──────────────────────┘
```

Everything runs via **Docker Compose**: `db` (postgres+pgvector), `backend` (FastAPI),
`frontend` (Next.js).

---

## 2. Core Principles

1. **Planner-first.** The LLM never answers cold. A LangGraph planner emits a structured
   plan (tools + rationale) that is both executed and surfaced to the user.
2. **Provider abstraction is load-bearing.** All model access goes through `LLMProvider`.
   Swapping providers changes one setting, not code. No `openai`/`anthropic`/etc. import
   exists outside `providers/`.
3. **Separation of concerns.** Routes are thin. Business logic lives in `services/`.
   The agent graph orchestrates services and tools; it holds no DB or vendor code.
4. **Grounded & cited.** Answers built from user documents carry citations with source
   spans. Web knowledge is labeled distinctly from note knowledge.
5. **Small, focused units.** Each module has one purpose and a clear interface; files
   are split before they sprawl.

---

## 3. Provider Abstraction

The single most important abstraction. Interface (in `providers/base.py`):

```python
class LLMProvider(Protocol):
    async def chat(self, messages, *, model, **opts) -> ChatResult: ...
    async def stream(self, messages, *, model, **opts) -> AsyncIterator[Chunk]: ...
    async def embed(self, texts, *, model) -> list[list[float]]: ...
    async def list_models(self) -> list[ModelInfo]: ...
    async def test_connection(self) -> ConnectionStatus: ...
```

- **Adapters:** `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`,
  `OpenRouterProvider`, `OllamaProvider` — each wraps its SDK/HTTP and normalizes to the
  shared result/chunk types.
- **Resolution:** a `ProviderFactory` builds the active provider **per request** from the
  user's `provider_settings` (decrypted key + chosen model). In dev, it falls back to
  `.env`.
- **Embeddings** flow through the same interface. Each document records the embedding
  **model and dimension** it was indexed with, so changing providers never silently
  corrupts vector search (mismatched dims are re-indexed, not compared).
- **Keys** are encrypted at rest (Fernet/app secret) and never returned to the client.

Consumers (RAG, planner, quiz, interview) depend only on `LLMProvider`.

---

## 4. Agent & Planner (LangGraph)

Every chat/interview/quiz turn runs a graph:

```
        ┌─────────┐
 user → │ Planner │ → structured Plan { tools:[...], reasoning }
        └────┬────┘
             │ conditional routing (by plan)
   ┌─────────┼───────────────┬───────────────┬───────────┐
   ▼         ▼               ▼               ▼           ▼
search_notes search_web  search_resume  search_memory  generate_quiz /
  (RAG)      (Phase 8)     (Phase 7)      (Phase 5)     make_revision
   └─────────┴───────────────┴───────────────┴───────────┘
                             │ collected tool outputs
                        ┌────▼─────┐
                        │ Synthesis│ → streamed answer + citations + plan trace
                        └──────────┘
```

- **Planner node** calls the LLM with a planning prompt and returns a validated
  `Plan` (Pydantic). It considers the question, workspace, and memory.
- **Tool nodes** are thin wrappers over services; each returns typed results with
  provenance (which document/URL/memory).
- **Synthesis node** composes the final answer, streams tokens, and attaches citations.
- The **plan trace** (tools chosen + why) is streamed to the right sidebar for
  transparency — this is a core product differentiator, not a debug view.

State is a typed `AgentState` (question, workspace, plan, tool_results, messages).

---

## 5. RAG Pipeline

```
question → query rewrite → embed(query) → pgvector similarity search (workspace-scoped)
        → top-k chunks → context assembly (with source spans) → LLM → answer + citations
```

- **Rewrite:** expand/disambiguate the query for better recall.
- **Retrieve:** cosine similarity in pgvector, filtered by workspace (and optionally
  document/subject), top-k with score threshold.
- **Assemble:** pack chunks under a token budget, preserving `{document, page, span}`
  so the synthesizer can cite precisely.
- **Cite:** answers reference sources inline; the UI links each citation to the chunk.

---

## 6. Document Pipeline

```
upload → validate → store file → extract text → extract metadata
      → intelligent chunk → embed (provider) → store chunks(vector) → status: ready
```

- **Extractors:** PyMuPDF (PDF), python-docx (DOCX), python-pptx (PPTX), plain (TXT),
  image path (Tesseract OCR — Phase 10).
- **Chunking:** structure-aware (headings/paragraphs/slides), token-bounded with overlap.
- **Async processing:** upload returns immediately; work runs in the background with
  status states (`queued → processing → ready → failed`) surfaced live in the UI.

---

## 7. Data Model (core tables)

| Table | Purpose |
|-------|---------|
| `users` | identity; email/password + OAuth links |
| `provider_settings` | per-user provider, encrypted key, model choices |
| `workspaces` | knowledge-base container, owned by a user |
| `documents` | uploaded file + metadata + processing status |
| `chunks` | text chunk, `vector` embedding, source span, page, embed-model/dim |
| `chat_sessions` / `messages` | conversation history |
| `memories` | weak topics, preferences, derived facts |
| `quiz_attempts` | quiz results feeding weak-topic memory |
| `interview_sessions` | mock-interview config, transcript, scores, feedback |

`chunks.embedding` is a pgvector column with an ivfflat/hnsw index. All content tables
are scoped by `workspace_id` and ultimately `user_id`.

---

## 8. Backend Layout

```
backend/app/
  api/         # FastAPI routers (thin): auth, workspaces, documents, chat, settings...
  agents/      # LangGraph graph, planner, tool nodes, agent state
  rag/         # query rewrite, retrieval, context assembly
  providers/   # LLMProvider interface + adapters + factory  (ONLY place with vendor SDKs)
  memory/      # memory service + retrieval for the planner
  services/    # business logic (auth, workspace, document, quiz, interview, chat)
  models/      # SQLAlchemy models + Pydantic schemas
  db/          # engine, session, migrations (Alembic)
  prompts/     # prompt templates (planner, synthesis, quiz, interview, resume)
  utils/       # shared helpers
  main.py      # app factory, middleware, router registration
```

## 9. Frontend Layout

```
frontend/
  app/            # App Router routes (auth, workspace, settings)
  components/     # reusable UI (shadcn-based), chat, sidebars, upload
  lib/            # api client, SSE streaming, auth, utils
  stores/         # client state
  styles/         # Tailwind + theme (dark-first, Inter, neutral + one accent)
```

**Layout:** left sidebar (workspaces · subjects · documents), center (chat · interview ·
quiz · revision · flashcards), right sidebar (sources · retrieved docs · memory · weak
topics · upload status), top nav (workspace selector · search · provider · settings ·
profile).

**Design language:** minimal, calm, high information density — Linear/Notion/Cursor, not
an AI-startup landing page. Neutral grayscale + one subtle accent, Inter, soft shadows,
purposeful motion only.

---

## 10. Security & Ops

- JWT auth; passwords hashed (argon2/bcrypt); OAuth via Authlib.
- Provider keys encrypted at rest; never sent back to the client.
- Per-workspace data isolation enforced in services.
- Docker Compose for local + as the deployment baseline; healthchecks on each service.
- Config via environment (`.env`), validated with pydantic-settings.

---

## 11. Build Phases

See [`../plan.md`](../plan.md) for the phased, checkbox-tracked build plan. Each phase is
designed to run end-to-end before the next begins.
