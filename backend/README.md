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

This is the current backend skeleton:

- PostgreSQL trip storage
- API contracts aligned with `docs/web-backend-data-contract.md`
- Thin background job bridge in `app/agent.py`
- Generation Agent workflow is being redesigned
- Editing Agent is temporarily disabled through a safe stub

## Generation Agent

The old generation graph has been removed. The API still keeps the same
frontend-facing contract:

```txt
POST /api/trips/{trip_id}/generate
GET  /api/jobs/{job_id}
```

For now, generation creates a placeholder itinerary so the workspace remains
available. The next step is to connect the redesigned LangGraph workflow behind
`app/agent.py`.
