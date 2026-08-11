# Travel Planner Backend

FastAPI backend for the travel planner web app.

## Run locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs:

```txt
http://127.0.0.1:8000/docs
```

Frontend can point to this backend with:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Current scope

Working today:

- PostgreSQL trip + itinerary + job storage (`db.py`, `orm_models.py`, `repository.py`)
- REST API aligned with `docs/web-backend-data-contract.md` (`main.py`, `models.py`)
- Background job lifecycle for generation (`agent.py`)

Available for the agent rewrite, not currently called:

- `llm.py` — DeepSeek JSON client with Langfuse tracing
- `amap.py` — AMap POI search / routing / weather, with fuzzy match filtering
- `observability.py` — Langfuse span + generation helpers

## Generation Agent

**The Generation Agent has been removed and is being redesigned from scratch.**

The frontend-facing contract is deliberately kept intact so the wizard and the
workspace still run end to end:

```txt
POST /api/trips/{trip_id}/generate   -> { tripId, jobId }
GET  /api/jobs/{job_id}              -> { status, progress, message }
```

`run_generation_job` in `app/agent.py` currently writes a placeholder itinerary.
That single call is the seam: the new agent plugs in there, and nothing else in
the API or the frontend needs to change.

The Editing Agent (`POST /api/trips/{trip_id}/edit`) was a no-op stub with no
frontend caller, so the route was removed entirely. It will come back as part of
the same redesign.
