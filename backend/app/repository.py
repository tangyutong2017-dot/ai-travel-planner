from copy import deepcopy
from datetime import UTC, datetime
import os
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .amap import AmapUnavailableError, search_poi
from .models import AgentJob, CreateTripPayload, Itinerary, Trip, TripListResponse, UpdateItineraryItemPayload
from .orm_models import AgentJobRecord, ItineraryRecord, TripRecord


ENABLE_DEMO_SEED = os.getenv("ENABLE_DEMO_SEED", "").lower() in {"1", "true", "yes"}


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def make_trip_id(destination: str) -> str:
    safe_destination = "".join(
        char for char in destination.strip().lower().replace(" ", "-")
        if char.isascii() and (char.isalnum() or char == "-")
    ).strip("-")
    return f"trip_{safe_destination or 'new'}_{uuid4().hex[:8]}"


def generate_trip_name(payload: CreateTripPayload) -> str:
    interests = payload.preferences.interests or []
    pace = payload.preferences.pace

    if pace <= 35:
        pace_word = "慢游"
    elif pace >= 75:
        pace_word = "深度快线"
    else:
        pace_word = "精选线"

    theme_words = []
    for interest in interests:
        if "自然" in interest:
            theme_words.append("风光")
        elif "美食" in interest:
            theme_words.append("美食")
        elif "文化" in interest or "历史" in interest:
            theme_words.append("人文")
        elif "亲子" in interest:
            theme_words.append("亲子")
        elif "购物" in interest:
            theme_words.append("城市")

    unique_themes = []
    for word in theme_words:
        if word not in unique_themes:
            unique_themes.append(word)

    theme = "".join(unique_themes[:2]) or "旅行"
    return f"{payload.destination}{theme}{pace_word}"


def cover_url_from_days(days: list) -> str | None:
    for day in days:
        if not isinstance(day, dict):
            continue

        for item in day.get("items", []):
            if not isinstance(item, dict):
                continue

            image_url = item.get("imageUrl")
            if isinstance(image_url, str) and image_url.strip():
                return image_url

    return None


LANDMARK_KEYWORDS = [
    ("西藏", "布达拉宫"),
    ("拉萨", "布达拉宫"),
    ("云南大理", "大理古城"),
    ("大理", "大理古城"),
    ("北京", "故宫博物院"),
    ("浙江杭州", "西湖"),
    ("杭州", "西湖"),
    ("四川成都", "宽窄巷子"),
    ("成都", "宽窄巷子"),
    ("上海", "外滩"),
    ("广西桂林", "漓江"),
    ("桂林", "漓江"),
]


def landmark_keyword_for_destination(destination: str) -> str:
    for keyword, landmark in LANDMARK_KEYWORDS:
        if keyword in destination or destination in keyword:
            return landmark

    return destination


def cover_url_from_landmark(destination: str) -> str | None:
    try:
        poi = search_poi(landmark_keyword_for_destination(destination), destination)
    except (AmapUnavailableError, httpx.HTTPError, ValueError):
        return None

    return poi.image_url if poi else None


def ensure_cover_url(record: TripRecord) -> bool:
    if record.cover_url:
        return False

    if record.itinerary:
        record.cover_url = cover_url_from_days(record.itinerary.days_json)

    if not record.cover_url:
        record.cover_url = cover_url_from_landmark(record.dest)

    return bool(record.cover_url)


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

    return TripListResponse(items=[trip_from_record(record) for record in records])


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


def get_itinerary(db: Session, trip_id: str) -> Itinerary | None:
    record = db.get(ItineraryRecord, trip_id)
    if not record:
        return None

    if fill_missing_poi_data(record):
        trip = db.get(TripRecord, trip_id)
        if trip:
            trip.cover_url = trip.cover_url or cover_url_from_days(record.days_json)
        db.commit()
        db.refresh(record)

    return itinerary_from_record(record)


def fill_missing_poi_data(record: ItineraryRecord) -> bool:
    days = deepcopy(record.days_json)
    changed = False

    for day in days:
        if not isinstance(day, dict):
            continue

        for item in day.get("items", []):
            if not isinstance(item, dict):
                continue
            if item.get("location") and item.get("poiId") and item.get("imageUrl"):
                continue

            try:
                poi = search_poi(str(item.get("title") or ""), record.destination)
            except (AmapUnavailableError, httpx.HTTPError, ValueError):
                poi = None

            if not poi:
                continue

            item["title"] = poi.name
            item["address"] = poi.address
            item["location"] = {"lat": poi.lat, "lng": poi.lng}
            item["poiId"] = poi.id
            item["source"] = "amap"
            item["imageUrl"] = item.get("imageUrl") or poi.image_url
            changed = True

    if changed:
        record.days_json = days

    return changed


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


def delete_itinerary_item(db: Session, trip_id: str, day_number: int, item_id: str) -> Itinerary | None:
    itinerary = get_itinerary(db, trip_id)
    if not itinerary:
        return None

    changed = False
    updated_days = []
    for day in itinerary.days:
        if day.day != day_number:
            updated_days.append(day)
            continue

        updated_items = [item for item in day.items if item.id != item_id]
        if len(updated_items) == len(day.items):
            updated_days.append(day)
            continue

        changed = True
        updated_budget = {
            **day.budget,
            "门票": sum_major_item_cost(updated_items),
        }
        updated_days.append(day.model_copy(update={"items": updated_items, "budget": updated_budget}))

    if not changed:
        return None

    updated_itinerary = itinerary.model_copy(update={"days": updated_days})
    save_itinerary(db, trip_id, updated_itinerary)
    return updated_itinerary


def update_itinerary_item(
    db: Session,
    trip_id: str,
    day_number: int,
    item_id: str,
    payload: UpdateItineraryItemPayload,
) -> Itinerary | None:
    itinerary = get_itinerary(db, trip_id)
    if not itinerary:
        return None

    patch = payload.model_dump(exclude_unset=True)
    if not patch:
        return itinerary

    changed = False
    updated_days = []
    for day in itinerary.days:
        if day.day != day_number:
            updated_days.append(day)
            continue

        updated_items = []
        for item in day.items:
            if item.id != item_id:
                updated_items.append(item)
                continue

            changed = True
            updated_items.append(item.model_copy(update=patch))

        updated_budget = {
            **day.budget,
            "门票": sum_major_item_cost(updated_items),
        }
        updated_days.append(day.model_copy(update={"items": updated_items, "budget": updated_budget}))

    if not changed:
        return None

    updated_itinerary = itinerary.model_copy(update={"days": updated_days})
    save_itinerary(db, trip_id, updated_itinerary)
    return updated_itinerary


def save_itinerary(db: Session, trip_id: str, itinerary: Itinerary, commit: bool = True) -> None:
    record = db.get(ItineraryRecord, trip_id)
    payload = {
        "destination": itinerary.destination,
        "title": itinerary.title,
        "date_range": itinerary.dateRange,
        "travelers": itinerary.travelers,
        "interests_json": itinerary.interests,
        "days_json": [day.model_dump() for day in itinerary.days],
    }

    if record:
        for key, value in payload.items():
            setattr(record, key, value)
    else:
        db.add(ItineraryRecord(trip_id=trip_id, **payload))

    trip = db.get(TripRecord, trip_id)
    if trip:
        trip.name = itinerary.title
        trip.dest = itinerary.destination
        trip.days = len(itinerary.days)
        trip.updated_at_label = now_iso()
        trip.attraction_count = count_major_itinerary_items(itinerary.days)
        trip.cover_url = trip.cover_url or cover_url_from_days(payload["days_json"])

    if commit:
        db.commit()


def create_agent_job(db: Session, trip_id: str) -> AgentJob:
    job_id = f"job_{uuid4().hex[:12]}"
    record = AgentJobRecord(
        id=job_id,
        trip_id=trip_id,
        status="queued",
        progress=8,
        message="任务已进入队列",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return job_from_record(record)


def get_agent_job(db: Session, job_id: str) -> AgentJob | None:
    record = db.get(AgentJobRecord, job_id)
    return job_from_record(record) if record else None


def update_agent_job(db: Session, job_id: str, status: str, progress: int, message: str) -> AgentJob | None:
    record = db.get(AgentJobRecord, job_id)
    if not record:
        return None

    record.status = status
    record.progress = progress
    record.message = message
    db.commit()
    db.refresh(record)
    return job_from_record(record)


def create_placeholder_itinerary(trip_id: str, payload: CreateTripPayload) -> Itinerary:
    traveler_count = payload.travelers.adults + payload.travelers.children + payload.travelers.infants
    interests = payload.preferences.interests or ["城市漫游", "美食探索"]

    return Itinerary(
        tripId=trip_id,
        destination=payload.destination,
        title=generate_trip_name(payload),
        dateRange=f"{payload.startDate} - {payload.endDate}",
        travelers=max(traveler_count, 1),
        interests=interests,
        days=[
            {
                "day": day,
                "date": f"第 {day} 天",
                "title": f"{payload.destination} Day {day}",
                "weather": {"icon": "☀️", "desc": "待查询", "range": "--", "tip": "天气数据将在后端接入后实时更新"},
                "budget": {"交通": 0, "餐饮": 0, "门票": 0, "其他": 0},
                "route": {"distanceKm": 0, "walkKm": 0, "transitKm": 0, "durationLabel": "待规划"},
                "items": [
                    {
                        "id": f"{trip_id}_d{day}_seed",
                        "startTime": "09:00",
                        "endTime": "11:00",
                        "title": f"围绕「{interests[(day - 1) % len(interests)]}」生成核心安排",
                        "type": "AI规划",
                        "durationLabel": "2h",
                        "cost": 0,
                        "reason": "当前为后端占位数据，下一步由 LangGraph agent 生成真实安排",
                    }
                ],
            }
            for day in range(1, payload.days + 1)
        ],
    )


def seed_initial_data(db: Session) -> None:
    if not ENABLE_DEMO_SEED:
        return

    if db.scalar(select(TripRecord.id).limit(1)):
        return

    seed_trips = [
        Trip(id="t1", name="云南大理慢旅行", dest="云南大理", days=5, date="2026.08.10", status="planned", attractionCount=12),
        Trip(id="t2", name="成都美食文化游", dest="四川成都", days=4, date="2026.09.05", status="planned", attractionCount=10),
        Trip(id="t3", name="杭州西湖周末游", dest="浙江杭州", days=3, date="2026.05.01", status="completed", attractionCount=8),
        Trip(id="t4", name="北京历史文化线", dest="北京", days=5, date="2026.04.20", status="completed", attractionCount=14),
        Trip(id="t5", name="上海城市漫游", dest="上海", days=3, date="2026.06.12", status="completed", attractionCount=9),
        Trip(id="t6", name="桂林山水轻旅行", dest="广西桂林", days=4, date="2026.07.18", status="planned", attractionCount=11),
    ]

    for trip in seed_trips:
        if db.get(TripRecord, trip.id):
            continue

        record = TripRecord(
            id=trip.id,
            name=trip.name,
            dest=trip.dest,
            days=trip.days,
            date=trip.date,
            status=trip.status,
            attraction_count=trip.attractionCount,
        )
        db.add(record)
        save_itinerary(db, trip.id, create_seed_itinerary(trip), commit=False)

    db.commit()


def create_seed_itinerary(trip: Trip) -> Itinerary:
    return Itinerary(
        tripId=trip.id,
        destination=trip.dest,
        title=trip.name,
        dateRange=f"{trip.date} 起",
        travelers=2,
        interests=["城市漫游", "美食探索", "文化体验"],
        days=[
            {
                "day": day,
                "date": f"第 {day} 天",
                "title": f"{trip.dest} Day {day}",
                "weather": {"icon": "☀️", "desc": "待查询", "range": "--", "tip": "真实天气将在后端接天气 API 后返回"},
                "budget": {"交通": 180, "餐饮": 260, "门票": 120, "其他": 80},
                "route": {"distanceKm": 8.4, "walkKm": 2.1, "transitKm": 6.3, "durationLabel": "~7h"},
                "items": [
                    {
                        "id": f"{trip.id}_d{day}_morning",
                        "startTime": "09:00",
                        "endTime": "11:30",
                        "title": f"{trip.dest} 核心区域探索",
                        "type": "城市",
                        "durationLabel": "2.5h",
                        "cost": 80,
                        "reason": "用于前端工作区联调的后端种子数据",
                    },
                    {
                        "id": f"{trip.id}_d{day}_afternoon",
                        "startTime": "14:00",
                        "endTime": "17:00",
                        "title": "兴趣点组合行程",
                        "type": "AI规划",
                        "durationLabel": "3h",
                        "cost": 120,
                        "reason": "下一步由 LangGraph agent 替换为真实 POI 和路线",
                        "transitFromPrev": "公共交通约 20 分钟",
                    },
                ],
            }
            for day in range(1, min(trip.days, 3) + 1)
        ],
    )
