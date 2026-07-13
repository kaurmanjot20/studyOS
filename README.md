# StudyOS

StudyOS is an interview-prep workspace I built to study from my own material instead of
generic chatbots. You drop in your notes, textbooks, slides and resume, and it helps you
prep for software engineering interviews using that material first, and the web only when
your notes don't cover something.

The thing I cared about most was that it shouldn't just be another "chat with a PDF"
wrapper. Every question you ask goes through a planner first. The planner looks at the
question (and what it knows about your weak spots) and decides how to answer: search your
notes, search the web, pull from memory, or read a file over MCP. Only then does it write
an answer, and it shows you which sources it used.

It's also not tied to any one AI provider. You bring your own key (OpenAI, Anthropic,
Gemini, OpenRouter, NVIDIA, or a local Ollama model), and if a hosted free tier starts
rate-limiting you mid-answer, it quietly falls back to a local model so you're never
stuck.

Runs entirely on your machine. No accounts, no login, single user.

## What it does

- Chat that plans before it answers, grounded in your documents with real citations
- A document pipeline that handles PDF, DOCX, PPTX, TXT and images (OCR), then chunks and
  embeds everything into pgvector
- Quizzes, flashcards and one-page revision sheets generated from your notes
- Mock interviews that ask questions, score your answers and give feedback
- Resume review and resume-based interview questions
- A memory of the topics you keep getting wrong, which the planner uses to prioritise
  revision (miss a quiz question, and that topic gets weighted up next time)
- Web search for the stuff your notes don't cover, kept clearly separate from your own
  material
- MCP support (filesystem and Notion) so the agent can reach beyond the database

## Stack

Frontend is Next.js (App Router) with Tailwind and shadcn/ui, dark mode by default.
Backend is FastAPI with async SQLAlchemy and Pydantic. Data lives in Postgres with the
pgvector extension for similarity search. The agent is built on LangGraph. Documents are
parsed with PyMuPDF, python-docx, python-pptx and Tesseract for OCR. Everything runs
through Docker Compose.

## How it works

Every chat turn runs a small LangGraph graph: plan, then retrieve, then stream the answer.
The planner returns a structured plan (which tools, and why), the retrieve step runs
whatever tools it picked (notes, web, memory, files), and the answer streams back from
whichever provider you've set, with citations attached. The plan and the sources show up
live in the right sidebar so you can see what it actually did.

All model access goes through one `LLMProvider` interface, so adding or switching
providers doesn't touch the rest of the code. The adapters talk to each API over plain
HTTP rather than pulling in five different SDKs. Chat and embeddings can even run on
different providers, which is handy when your chat provider has no embeddings endpoint
(OpenRouter, for example) and you want embeddings to run locally on Ollama.

## Running it

```bash
cp .env.example .env
docker compose up --build
```

Then open http://localhost:3000. The API and its docs live at http://localhost:8000/docs.
Everything binds to localhost only, so nothing is exposed to the rest of your network.

You can leave the defaults for a quick local run, but you'll want to open Settings (gear,
top right) and point it at an AI provider with your own key. Hit Test Connection, then
make a workspace and upload some notes.

One gotcha: if you change something in `.env`, restart with `docker compose up -d backend`
rather than `docker compose restart` — a plain restart won't reload the env file.

### Using local models (no key needed)

If you'd rather not deal with API keys or rate limits, install
[Ollama](https://ollama.com/download) and pull a couple of models:

```bash
ollama pull llama3.2         # chat
ollama pull nomic-embed-text # embeddings
```

The backend reaches Ollama on the host through `host.docker.internal`. This is also what
the automatic fallback uses when a hosted provider throttles you.

## Configuration

The important settings in `.env` (full list in `.env.example`):

- `DEFAULT_LLM_PROVIDER` / `DEFAULT_LLM_MODEL` — what to use when nothing's set in Settings
- `EMBEDDING_PROVIDER`, `DEFAULT_EMBEDDING_MODEL`, `EMBEDDING_DIM` — the embedding model
  and its vector size. If you change the dimension you have to recreate the DB volume
  (`docker compose down -v`), since the pgvector column is a fixed size
- `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `NVIDIA_API_KEY` — provider
  keys (you can also just enter these in Settings, where they're encrypted)
- `ENABLE_LOCAL_FALLBACK`, `FALLBACK_MODEL` — the local model to fall back to on rate limits
- `ENCRYPTION_KEY` — used to encrypt provider keys stored in the database
- `NOTION_API_KEY` — only needed if you want the Notion MCP server

Provider keys you enter in the app are encrypted before they hit the database, and the
services only ever bind to localhost, so nothing is exposed to your network.

## Project layout

```
backend/app/
  api/         thin FastAPI routers, one per feature
  agents/      the LangGraph graph, planner and agent state
  rag/         extraction, chunking, retrieval
  providers/   the LLMProvider interface, adapters and fallback (the only place that
               talks to vendor APIs)
  memory/      long-term memory
  services/    the actual business logic
  models/      SQLAlchemy models and Pydantic schemas
  prompts/     prompt templates
  core/        config and key encryption
  alembic/     migrations
frontend/
  app/         routes and global styles
  components/  the three-pane shell, chat, study, interview, settings
  lib/         API client, the SSE chat stream, types
```

## A few dev notes

- Backend code is bind-mounted and reloads on save. Migrations run automatically when the
  container starts; to run one by hand, `docker compose exec backend alembic upgrade head`.
- The frontend runs `next dev` inside its container with hot reload. If you want to run it
  bare with `npm run dev`, don't leave the Docker one running too, they'll fight over
  port 3000.
- Logs: `docker compose logs -f`.
- Your data lives in a Docker volume, so it survives restarts. `docker compose down` keeps
  it; only `docker compose down -v` wipes it.

## Upcoming

Things I still want to add:

- Streaming for quiz and interview generation (right now they generate in one shot)
- A bigger catalog of MCP servers, configurable per workspace
- Proper spaced repetition for the flashcards
- Speaking your interview answers instead of typing them
- Exporting revision sheets to PDF or straight into Notion
