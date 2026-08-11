"""行程详情的读写：取详情、POI 补全、单项编辑与删除、整体保存。"""

from copy import deepcopy

import httpx
from sqlalchemy.orm import Session

from ..amap import AmapUnavailableError, search_poi
from ..models import Itinerary, UpdateItineraryItemPayload
from ..orm_models import ItineraryRecord, TripRecord
from .covers import cover_url_from_days
from .mappers import count_major_itinerary_items, itinerary_from_record, sum_major_item_cost
from .naming import now_iso


PLACEHOLDER_SOURCE = "placeholder"


def is_placeholder_item(item: dict) -> bool:
    """占位条目没有真实景点名，不能拿去高德搜索。

    新数据靠 source 标记识别；`_seed` 后缀是给标记落地之前的历史数据兜底。
    """
    return item.get("source") == PLACEHOLDER_SOURCE or str(item.get("id") or "").endswith("_seed")


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
            # 用「围绕「自然风光」生成核心安排」这种标题去搜，会匹配到无关 POI，
            # 于是界面上出现假评分和假坐标。
            if is_placeholder_item(item):
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
