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
        title=record.title,
        dateRange=record.date_range,
        originCity=record.origin_city,
        destination=record.destination,
        route=record.route_json or [record.destination],
        travelers=record.travelers_json,
        interests=record.interests_json,
        notes=record.notes_json or [],
        bookings=record.bookings_json or [],
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


# 「主要景点」= 景点与活动。原先靠 countsAsMajorPlace 布尔位标记，
# 现在由 stopType 直接推导，少一个可能与类型矛盾的字段。
MAJOR_STOP_TYPES = {"sight", "activity"}


def count_major_itinerary_items(days: list) -> int:
    total = 0
    for day in days:
        items = getattr(day, "items", []) if not isinstance(day, dict) else day.get("items", [])
        for item in items:
            stop_type = item.get("stopType") if isinstance(item, dict) else item.stopType
            if stop_type in MAJOR_STOP_TYPES:
                total += 1

    return total


def trip_date_sort_value(record: TripRecord) -> str:
    return record.date.replace(".", "-")
