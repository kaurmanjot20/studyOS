# InterviewOS — Build Plan

An AI-powered interview-preparation workspace. Planner-first agent, RAG over the user's
own documents, provider-agnostic LLMs (bring your own key), memory of weak topics, mock
interviews, and study-artifact generation.

This file is the **living checklist**. Each phase is built to run end-to-end before the
next begins. Check items off as they land; keep the "Status" line current.

**Status:** Phase 0 in progress.
**Repo:** https://github.com/kaurmanjot20/studyOS.git
**Design doc:** [`docs/architecture.md`](docs/architecture.md)

Legend: `[ ]` todo · `[~]` in progress · `[x]` done

---

## Phase 0 — Foundation & Scaffold
Goal: `docker compose up` brings up Postgres+pgvector, FastAPI, and Next.js; health checks green.

- [ ] Repo scaffold: `backend/`, `frontend/`, `docker/`, `docs/`, root tooling
- [ ] `.gitignore`, `.env.example`, `README` stub
- [ ] Backend skeleton: FastAPI app, settings (pydantic-settings), `/health` route
- [ ] Layered package layout: `api/ agents/ rag/ providers/ memory/ services/ models/ db/ prompts/ utils/`
- [ ] DB layer: SQLAlchemy async engine, session dependency, Alembic init
- [ ] Postgres + pgvector Docker service; enable `vector` extension via migration
- [ ] Frontend skeleton: Next.js App Router + Tailwind + shadcn/ui, base theme (dark-first)
- [ ] `docker-compose.yml` wiring db + backend + frontend; healthchecks
- [ ] Makefile / npm scripts for common tasks
- [ ] Commit: `chore: scaffold monorepo and docker compose foundation`

## Phase 1 — Auth & Workspaces
Goal: sign in, create/select workspaces, see the 3-pane app shell.

- [ ] User model + migration
- [ ] Email/password auth: hashing (argon2/bcrypt), register/login, JWT issue/verify
- [ ] Google OAuth flow (Authlib) + account linking
- [ ] Auth middleware / `get_current_user` dependency
- [ ] Workspace model + CRUD service + routes (scoped to user)
- [ ] Frontend auth pages, session handling, protected routes
- [ ] App shell: left sidebar (workspaces/subjects/documents), center, right sidebar, top nav
- [ ] Commit: `feat(auth): add email/password and Google OAuth with JWT`
- [ ] Commit: `feat(workspaces): add workspace CRUD and app shell`

## Phase 2 — Provider Abstraction & Settings
Goal: user configures any provider with their own key and passes Test Connection.

- [ ] `LLMProvider` interface: `chat`, `stream`, `embed`, `test_connection`, `list_models`
- [ ] Adapters: OpenAI, Anthropic, Gemini, OpenRouter, Ollama
- [ ] Provider registry + factory resolving from user settings (fallback to `.env` in dev)
- [ ] Encrypted storage of user API keys (`provider_settings` table)
- [ ] Embedding provider selection; per-document embedding-model + dimension tracking
- [ ] Settings API: save config, list models, test connection
- [ ] Settings UI: provider select, key input, model select, Test Connection + status
- [ ] Commit: `feat(providers): add provider-agnostic LLM abstraction and adapters`
- [ ] Commit: `feat(settings): add AI provider settings with connection test`

## Phase 3 — Document Upload & Pipeline
Goal: drop a file → it's parsed, chunked, embedded, and searchable, with live status.

- [ ] Document + chunk models (chunk holds `vector`, source span, page)
- [ ] Upload endpoint (multipart), file storage, size/type validation
- [ ] Extractors: PDF (PyMuPDF), DOCX (python-docx), PPTX (python-pptx), TXT, images (stub→OCR later)
- [ ] Metadata extraction (title, pages, word count)
- [ ] Intelligent chunking (structure-aware, overlap, token-bounded)
- [ ] Embedding generation via provider abstraction; batch + store in pgvector
- [ ] Background processing (task queue / background tasks) + status states
- [ ] Frontend: drag-and-drop upload, progress, processing status, document list
- [ ] Commit: `feat(documents): add upload and background processing pipeline`
- [ ] Commit: `feat(rag): add extraction, chunking, and embedding storage`

## Phase 4 — RAG + Planner + Chat  ★ intelligence core
Goal: ask a question → planner routes → RAG answers with citations, streamed, with a visible plan trace.

- [ ] Query rewriting node
- [ ] Vector search service (workspace-scoped similarity, top-k, filters)
- [ ] Context assembly with source spans for citation
- [ ] LangGraph graph: Planner → tool nodes → synthesis → stream
- [ ] Planner: structured plan output (which tools + rationale)
- [ ] Tool: `search_notes` (RAG); stubs for `search_web`, `search_resume`, `search_memory`
- [ ] Streaming chat endpoint (SSE); message + session persistence
- [ ] Frontend chat: streaming, markdown, code highlighting, citations
- [ ] Right sidebar: retrieved sources + planner trace
- [ ] Commit: `feat(agent): add LangGraph planner with tool routing`
- [ ] Commit: `feat(chat): add streaming RAG chat with citations`

## Phase 5 — Memory
Goal: the planner consults memory (weak topics, history, preferences) before answering.

- [ ] Memory model(s): weak topics, quiz/interview history, preferences
- [ ] Memory service: write on quiz/interview outcomes, read for planning
- [ ] `search_memory` tool wired into planner
- [ ] Prioritization logic (e.g., surface repeatedly-missed topics)
- [ ] Right-sidebar memory / weak-topics panel
- [ ] Commit: `feat(memory): add long-term memory and planner integration`

## Phase 6 — Study Artifacts (Quiz · Flashcards · Revision)
Goal: generate quizzes, flashcards, and revision notes grounded in the user's docs.

- [ ] Quiz generator: MCQ / short / long / follow-up, adaptive difficulty, dedupe
- [ ] Quiz UI + attempt scoring → writes weak topics to memory
- [ ] Flashcard generation from documents + review UI
- [ ] Revision notes / one-page cheat sheet generation
- [ ] Commit: `feat(quiz): add adaptive quiz generation and scoring`
- [ ] Commit: `feat(study): add flashcards and revision-note generation`

## Phase 7 — Interview & Resume Modes
Goal: resume-based Q&A/review and a full mock-interview conductor with feedback + history.

- [ ] Resume ingestion (uses doc pipeline) + resume-aware tool
- [ ] Resume mode: project questions, follow-ups, review + improvement suggestions
- [ ] Mock interview config (company, difficulty, subject, duration)
- [ ] Interview conductor graph: ask → evaluate → follow-up → track weak areas
- [ ] Feedback + performance history persistence
- [ ] Interview UI + history view
- [ ] Commit: `feat(resume): add resume-based question generation and review`
- [ ] Commit: `feat(interview): add mock interview mode with scoring and history`

## Phase 8 — Web Search Tool
Goal: when notes are insufficient, planner searches the web and merges, clearly labeled.

- [ ] Web search service (trusted-source search + fetch)
- [ ] Summarization + merge with note context
- [ ] `search_web` tool wired into planner (planner decides when to use it)
- [ ] UI distinguishes note-sourced vs web-sourced knowledge
- [ ] Commit: `feat(websearch): add web search tool with source attribution`

## Phase 9 — MCP Integration
Goal: filesystem + Notion MCP servers, with an extensible registry for future servers.

- [ ] MCP client integration + server registry
- [ ] Filesystem MCP server wiring
- [ ] Notion MCP server wiring
- [ ] Expose MCP tools to the planner
- [ ] Settings UI for enabling/configuring MCP servers
- [ ] Commit: `feat(mcp): add filesystem and Notion MCP integration`

## Phase 10 — OCR, Polish & Docs
Goal: OCR for images, production hardening, and complete documentation.

- [ ] Tesseract OCR in the image extractor path
- [ ] Toasts, keyboard shortcuts, loading skeletons, responsive passes
- [ ] Error handling, rate limits, input validation hardening
- [ ] README, architecture diagram, folder guide, env setup, docker guide, dev guide, roadmap
- [ ] Commit: `feat(ocr): add Tesseract OCR for image documents`
- [ ] Commit: `docs: add full documentation and architecture diagram`

---

## Cross-cutting (maintained across phases)
- [ ] Business logic in `services/`, never in routes
- [ ] No vendor SDK imported outside `providers/`
- [ ] Type hints + Pydantic schemas at boundaries
- [ ] Reasonable tests for services and the agent graph
- [ ] Keep files focused; split when they grow
