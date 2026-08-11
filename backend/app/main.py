from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .agent import get_generation_job, run_generation_job, start_generation_job
from .db import get_db, init_db, SessionLocal
from .editing_graph import edit_itinerary
from .models import (
    AgentJob,
    CreateTripPayload,
    CreateTripResponse,
    EditItineraryPayload,
    EditItineraryResponse,
    GenerateTripResponse,
    Itinerary,
    Trip,
    TripListResponse,
    TripStatus,
    UpdateItineraryItemPayload,
    UpdateTripPayload,
)
from .repository import create_trip, delete_itinerary_item, delete_trip, get_itinerary, get_trip, list_trips, save_itinerary, seed_initial_data, update_itinerary_item, update_trip_name


app = FastAPI(title="Travel Planner API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/trips", response_model=TripListResponse)
def get_trips(
    status: TripStatus | None = Query(default=None),
    keyword: str | None = Query(default=None),
    sort: str = Query(default="updatedAt_desc"),
    db: Session = Depends(get_db),
) -> TripListResponse:
    return list_trips(db, status=status, keyword=keyword, sort=sort)


@app.post("/api/trips", response_model=CreateTripResponse)
def post_trip(payload: CreateTripPayload, db: Session = Depends(get_db)) -> CreateTripResponse:
    trip = create_trip(db, payload)
    return CreateTripResponse(tripId=trip.id)


@app.get("/api/trips/{trip_id}", response_model=Itinerary)
def get_trip_detail(trip_id: str, db: Session = Depends(get_db)) -> Itinerary:
    itinerary = get_itinerary(db, trip_id)
    if itinerary:
        return itinerary

    if not get_trip(db, trip_id):
        raise HTTPException(status_code=404, detail="Trip not found")

    raise HTTPException(status_code=409, detail="Trip itinerary has not been generated")


@app.delete("/api/trips/{trip_id}")
def delete_trip_route(trip_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    if not delete_trip(db, trip_id):
        raise HTTPException(status_code=404, detail="Trip not found")

    return {"tripId": trip_id}


@app.patch("/api/trips/{trip_id}", response_model=Trip)
def update_trip_route(
    trip_id: str,
    payload: UpdateTripPayload,
    db: Session = Depends(get_db),
) -> Trip:
    updated = update_trip_name(db, trip_id, payload.name)
    if not updated:
        raise HTTPException(status_code=404, detail="Trip not found")

    return updated


@app.delete("/api/trips/{trip_id}/days/{day_number}/items/{item_id}", response_model=Itinerary)
def delete_trip_item_route(
    trip_id: str,
    day_number: int,
    item_id: str,
    db: Session = Depends(get_db),
) -> Itinerary:
    updated = delete_itinerary_item(db, trip_id, day_number, item_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Itinerary item not found")

    return updated


@app.patch("/api/trips/{trip_id}/days/{day_number}/items/{item_id}", response_model=Itinerary)
def update_trip_item_route(
    trip_id: str,
    day_number: int,
    item_id: str,
    payload: UpdateItineraryItemPayload,
    db: Session = Depends(get_db),
) -> Itinerary:
    updated = update_itinerary_item(db, trip_id, day_number, item_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Itinerary item not found")

    return updated


@app.post("/api/trips/{trip_id}/edit", response_model=EditItineraryResponse)
def edit_trip_route(
    trip_id: str,
    payload: EditItineraryPayload,
    db: Session = Depends(get_db),
) -> EditItineraryResponse:
    itinerary = get_itinerary(db, trip_id)
    if not itinerary:
        if not get_trip(db, trip_id):
            raise HTTPException(status_code=404, detail="Trip not found")
        raise HTTPException(status_code=409, detail="Trip itinerary has not been generated")

    try:
        message, updated = edit_itinerary(itinerary, payload.instruction, payload.activeDay)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Editing Agent failed: {exc}") from exc

    save_itinerary(db, trip_id, updated)
    return EditItineraryResponse(message=message, itinerary=updated)


@app.post("/api/trips/{trip_id}/generate", response_model=GenerateTripResponse)
def generate_trip(
    trip_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> GenerateTripResponse:
    if not get_trip(db, trip_id):
        raise HTTPException(status_code=404, detail="Trip not found")

    job = start_generation_job(trip_id)
    background_tasks.add_task(run_generation_job, job.jobId)
    return GenerateTripResponse(tripId=trip_id, jobId=job.jobId)


@app.get("/api/jobs/{job_id}", response_model=AgentJob)
def get_job(job_id: str) -> AgentJob:
    job = get_generation_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
