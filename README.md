# Ishita HQ — AI Task Manager

A personal operating system for Ishita: drop in any raw task or thought in
plain language, and it gets automatically classified into one of seven
life/work buckets, given a priority and a due timing, and surfaced on a
dashboard alongside an AI-generated daily brief.

This is the **Phase 1 (Core Foundation)** build. See
[PHASE1_WALKTHROUGH.md](PHASE1_WALKTHROUGH.md) for what's done, what's
known-limited, and how to demo it.

## Stack

- **Backend**: FastAPI + Postgres (`psycopg`), Groq (Llama 3.3 70B) for classification and brief generation
- **Frontend**: React + Vite, no extra UI framework
- **Package management**: `uv` for Python, `npm` for the frontend

## Project layout

```
backend/
  agents/         classifier_agent.py, brief_agent.py — the two LLM call sites
  services/       business logic; routers never touch the DB directly
  routers/        FastAPI route handlers (tasks, students, brief)
  models/         Pydantic schemas
  db/             connection.py + schema.sql
  tests/          pytest suite (deterministic logic only, no DB/LLM calls)
frontend/
  src/App.jsx     the whole dashboard UI (single file by design at this scale)
  src/lib/api.js  fetch wrappers for every backend endpoint
```

## Setup

### 1. Database

Create a Postgres database, then run the schema once:

```powershell
psql -h localhost -U postgres -c "CREATE DATABASE ishita_hq"
psql -h localhost -U postgres -d ishita_hq -f backend/db/schema.sql
```

### 2. Backend environment

Copy `backend/.env.example` to `backend/.env` and fill in:

```
DATABASE_URL=postgresql://postgres:<password>@localhost:5432/ishita_hq
GROQ_API_KEY=<your key from console.groq.com/keys>
CORS_ORIGIN=http://localhost:5173
```

### 3. Install dependencies

```powershell
uv sync                          # Python deps, from repo root
cd frontend; npm install; cd ..  # frontend deps
```

### 4. Run it

Two terminals:

```powershell
# Terminal 1 — backend
cd backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open the URL Vite prints (`http://localhost:5173`).

### 5. Run the tests

```powershell
cd backend
python -m pytest tests/ -v
```

## How it works, in short

1. Type anything into the capture bar → `POST /api/tasks/` → the
   classifier agent ([backend/agents/classifier_agent.py](backend/agents/classifier_agent.py))
   sends it to the LLM with the bucket/sub-bucket/people/student list, gets
   back a structured classification, and the task is inserted.
2. The dashboard ([frontend/src/App.jsx](frontend/src/App.jsx)) shows seven
   bucket boards, sorted by priority within each board.
3. The daily brief ([backend/services/brief_service.py](backend/services/brief_service.py))
   does all counting/aggregation in plain SQL — only the narrative
   phrasing goes through the LLM ([backend/agents/brief_agent.py](backend/agents/brief_agent.py)),
   so the numbers are never at risk of LLM error.
4. `due` labels ("today", "this week") are relative, not absolute dates —
   [backend/services/due_utils.py](backend/services/due_utils.py) recomputes
   them on every read so a task left open past its window flips to
   "overdue" automatically.
