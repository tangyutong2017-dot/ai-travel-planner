"""行程本身的读写：列表、筛选、统计、创建、改名、删除。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CreateTripPayload, Trip, TripListResponse, TripListSummary
from ..orm_models import ItineraryRecord, TripRecord
from .covers import cover_url_from_landmark, ensure_cover_url
from .mappers import trip_date_sort_value, trip_from_record
from .naming import make_trip_id, generate_trip_name, now_iso


def list_trips(db: Session, status: str | None = None, keyword: str | None = None, sort: str = "updatedAt_desc") -> TripListResponse:
    all_records = list(db.scalars(select(TripRecord)).all())
    cover_changed = False
    for record in all_records:
        cover_changed = ensure_cover_url(record) or cover_changed

    if cover_changed:
        db.commit()

    records = all_records

    if status:
        records = [trip for trip in records if trip.status == status]

    if keyword:
        query = keyword.strip().lower()
        records = [trip for trip in records if query in trip.name.lower() or query in trip.dest.lower()]

    if sort == "startDate_desc":
        records.sort(key=trip_date_sort_value, reverse=True)
    elif sort == "days_desc":
        records.sort(key=lambda trip: trip.days, reverse=True)
    else:
        records.sort(key=lambda trip: trip.updated_at or trip.created_at, reverse=True)

    items = [trip_from_record(record) for record in records]
    return TripListResponse(items=items, summary=summarize_trips(items))


def summarize_trips(items: list[Trip]) -> TripListSummary:
    """Aggregate the trips that are actually being returned.

    The summary describes the filtered result set, not the whole library, so
    ``summary.total`` always equals ``len(items)``.
    """
    return TripListSummary(
        total=len(items),
        planned=sum(1 for trip in items if trip.status == "planned"),
        completed=sum(1 for trip in items if trip.status == "completed"),
        totalDays=sum(trip.days for trip in items),
        destinationCount=len({trip.dest for trip in items}),
        attractionCount=sum(trip.attractionCount or 0 for trip in items),
    )


def get_trip(db: Session, trip_id: str) -> Trip | None:
    record = db.get(TripRecord, trip_id)
    return trip_from_record(record) if record else None


def delete_trip(db: Session, trip_id: str) -> bool:
    record = db.get(TripRecord, trip_id)
    if not record:
        return False

    db.delete(record)
    db.commit()
    return True


def get_trip_payload(db: Session, trip_id: str) -> CreateTripPayload | None:
    record = db.get(TripRecord, trip_id)
    if not record or not record.payload_json:
        return None
    return CreateTripPayload.model_validate(record.payload_json)


def create_trip(db: Session, payload: CreateTripPayload) -> Trip:
    trip_id = make_trip_id(payload.destination)
    trip_name = generate_trip_name(payload)
    record = TripRecord(
        id=trip_id,
        name=trip_name,
        dest=payload.destination,
        days=payload.days,
        date=payload.startDate,
        status="planned",
        cover_url=cover_url_from_landmark(payload.destination),
        updated_at_label=now_iso(),
        attraction_count=0,
        payload_json=payload.model_dump(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return trip_from_record(record)


def update_trip_name(db: Session, trip_id: str, name: str) -> Trip | None:
    record = db.get(TripRecord, trip_id)
    if not record:
        return None

    clean_name = name.strip()
    record.name = clean_name
    record.updated_at_label = now_iso()

    itinerary_record = db.get(ItineraryRecord, trip_id)
    if itinerary_record:
      itinerary_record.title = clean_name

    db.commit()
    db.refresh(record)
    return trip_from_record(record)
