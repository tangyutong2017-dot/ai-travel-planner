"""ORM 记录 ↔ Pydantic 模型的映射，以及列表页用到的聚合计算。"""

from ..models import AgentJob, Itinerary, Trip
from ..orm_models import AgentJobRecord, ItineraryRecord, TripRecord
from .covers import cover_url_from_days, ensure_cover_url


def trip_from_record(record: TripRecord) -> Trip:
    derived_cover_url = None
    if record.itinerary:
        derived_cover_url = cover_url_from_days(record.itinerary.days_json)

    return Trip(
        id=record.id,
        name=record.name,
        dest=record.dest,
        days=record.days,
        date=record.date,
        status=record.status,  # type: ignore[arg-type]
        coverUrl=record.cover_url or derived_cover_url,
        updatedAt=record.updated_at_label,
        attractionCount=record.attraction_count,
    )


def itinerary_from_record(record: ItineraryRecord) -> Itinerary:
    return Itinerary(
        tripId=record.trip_id,
        destination=record.destination,
        title=record.title,
        dateRange=record.date_range,
        travelers=record.travelers,
        interests=record.interests_json,
        days=record.days_json,
    )


def job_from_record(record: AgentJobRecord) -> AgentJob:
    return AgentJob(
        jobId=record.id,
        tripId=record.trip_id,
        status=record.status,  # type: ignore[arg-type]
        progress=record.progress,
        message=record.message,
    )


def count_major_itinerary_items(days: list) -> int:
    total = 0
    for day in days:
        items = getattr(day, "items", []) if not isinstance(day, dict) else day.get("items", [])
        for item in items:
            if isinstance(item, dict):
                if item.get("countsAsMajorPlace", True) and not item.get("mealType"):
                    total += 1
                continue

            if item.countsAsMajorPlace and not item.mealType:
                total += 1

    return total


def sum_major_item_cost(items: list) -> int:
    total = 0
    for item in items:
        if item.countsAsMajorPlace and not item.mealType:
            total += item.cost
    return total


def trip_date_sort_value(record: TripRecord) -> str:
    return record.date.replace(".", "-")
