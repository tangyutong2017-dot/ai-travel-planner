"""行程详情的读写：取详情、POI 补全、单项编辑与删除、整体保存。"""

from copy import deepcopy
from math import cos, radians, sqrt

import httpx
from sqlalchemy.orm import Session

from ..amap import AmapUnavailableError, search_poi
from ..models import Itinerary, UpdateItineraryItemPayload
from ..orm_models import ItineraryRecord, TripRecord
from .covers import cover_url_from_days
from .mappers import count_major_itinerary_items, itinerary_from_record
from .naming import now_iso


PLACEHOLDER_SOURCE = "placeholder"


def is_placeholder_item(item: dict) -> bool:
    """占位条目没有真实景点名，不能拿去高德搜索。

    靠 verification 标记识别；`source` 是旧字段、`_seed` 后缀是更早的历史数据，
    两者都保留作兜底。
    """
    return (
        item.get("verification") == PLACEHOLDER_SOURCE
        or item.get("source") == PLACEHOLDER_SOURCE
        or str(item.get("id") or "").endswith("_seed")
    )


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


# 只有真实地点才值得拿去高德搜索。航班、转移这类条目没有对应 POI，
# 用「机场专车 → 大理古城」去搜只会匹配到无关结果。
POI_SEARCHABLE_TYPES = {"sight", "food", "activity", "hotel"}

# 条目已有坐标时，用它校验高德匹配。超过这个距离视为匹配错误而非补全。
MAX_MATCH_DISTANCE_KM = 3.0


def rough_distance_km(a: dict, b: dict) -> float:
    """等距圆柱近似。城市尺度下足够判断「是不是同一个地方」。"""
    lat_mid = radians((a["lat"] + b["lat"]) / 2)
    dx = (b["lng"] - a["lng"]) * cos(lat_mid)
    dy = b["lat"] - a["lat"]
    return sqrt(dx * dx + dy * dy) * 111.0


def fill_missing_poi_data(record: ItineraryRecord) -> bool:
    """用高德补全缺失的 POI 信息。

    补全，不是覆盖——作者写的标题与坐标一律保留：
    - 标题携带意图（「大理古城 · 人民路与复兴路」比「大理古城」信息量大）
    - 已有坐标是判断高德是否匹配错的依据
    """
    days = deepcopy(record.days_json)
    changed = False

    for day in days:
        if not isinstance(day, dict):
            continue

        for item in day.get("items", []):
            if not isinstance(item, dict):
                continue
            if item.get("stopType") not in POI_SEARCHABLE_TYPES:
                continue
            if is_placeholder_item(item):
                continue
            if item.get("poiId") and item.get("imageUrl") and item.get("location"):
                continue

            try:
                poi = search_poi(str(item.get("title") or ""), record.destination)
            except (AmapUnavailableError, httpx.HTTPError, ValueError):
                poi = None

            if not poi:
                continue

            poi_location = {"lat": poi.lat, "lng": poi.lng}
            existing = item.get("location")

            # 已有坐标时，高德若指向别处，说明匹配到了同名或近名的其他地点。
            # 此时保留原坐标并标为未核实，而不是把行程挪到几十公里外。
            if existing and rough_distance_km(existing, poi_location) > MAX_MATCH_DISTANCE_KM:
                if item.get("verification") != "unverified":
                    item["verification"] = "unverified"
                    changed = True
                continue

            if not item.get("location"):
                item["location"] = poi_location
            if not item.get("address"):
                item["address"] = poi.address
            if not item.get("imageUrl"):
                item["imageUrl"] = poi.image_url
            item["poiId"] = poi.id
            item["verification"] = "verified"
            changed = True

    if changed:
        record.days_json = days

    return changed


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
        updated_days.append(day.model_copy(update={"items": updated_items}))

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

        updated_days.append(day.model_copy(update={"items": updated_items}))

    if not changed:
        return None

    updated_itinerary = itinerary.model_copy(update={"days": updated_days})
    save_itinerary(db, trip_id, updated_itinerary)
    return updated_itinerary


def save_itinerary(db: Session, trip_id: str, itinerary: Itinerary, commit: bool = True) -> None:
    record = db.get(ItineraryRecord, trip_id)
    payload = {
        "origin_city": itinerary.originCity,
        "destination": itinerary.destination,
        "title": itinerary.title,
        "date_range": itinerary.dateRange,
        "travelers_json": itinerary.travelers.model_dump(),
        "route_json": itinerary.route,
        "interests_json": itinerary.interests,
        "notes_json": [note.model_dump() for note in itinerary.notes],
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
