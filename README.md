# customer-support-bot

RAG chatbot for customer support. FastAPI + LangChain + ChromaDB, runs in two docker containers.

## Run it

```bash
cp .env.example .env       # add OPENAI_API_KEY or GOOGLE_API_KEY (optional)
docker compose up --build
```

Then open http://localhost:8080, hit **Load sample KB** in the sidebar, and start asking questions.

If you don't set an API key the bot runs in demo mode — no LLM call, just returns the best-matching chunk from your docs. Useful for trying it out or testing the retrieval pipeline.

## What's in here

```
backend/   FastAPI service (port 8000)
frontend/  Static chat UI served by nginx (port 8080)
data/      Sample knowledge base docs (markdown)
```

The chat UI is plain HTML/CSS/JS. nginx proxies `/api/*` to the backend container.

Swagger UI at http://localhost:8080/api/docs.

## How the pieces fit

1. Docs are split into ~800-char chunks and embedded locally with `sentence-transformers/all-MiniLM-L6-v2` (no API call, runs on CPU)
2. Vectors go into ChromaDB (embedded mode, persisted to a docker volume)
3. On a user question: embed query → cosine search top 4 chunks → send chunks + question to the LLM with a "cite your sources, don't make stuff up" prompt
4. Return the answer + the chunks (so the UI can show clickable source chips)

## Swap the LLM

Set `OPENAI_API_KEY` for GPT, `GOOGLE_API_KEY` for Gemini, or leave both unset for demo mode. OpenAI wins if both are set. Add new providers in `backend/app/llm.py`.

## Dev mode (no docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed_on_startup
uvicorn app.main:app --reload --port 8000

# in another terminal
cd frontend
python -m http.server 8080
```

You'll need to point `app.js` at `http://localhost:8000` directly (or just keep using docker).

## Adding your own docs

Either drop `.md`/`.txt` files into `backend/data/` and re-run `seed_on_startup.py`, or hit `/ingest/file` from the UI. For PDFs/DOCX you need the file upload route — the seed script only handles text.

## TODO (things I'd do next)

- proper structured logging (using `print()` everywhere is a smell)
- chat history per session_id (currently stateless)
- rate limiting on /chat
- a real eval set + automated quality checks
- swap the demo LLM fallback for something like Ollama so it works offline for real
- websocket instead of HTTP for streaming tokens
