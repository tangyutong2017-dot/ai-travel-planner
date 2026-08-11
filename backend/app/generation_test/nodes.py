from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta
from typing import Any, TypedDict
from uuid import uuid4

from ..amap import AmapUnavailableError, driving_route, search_pois, weather_for_city
from ..llm import deepseek_json as raw_deepseek_json
from ..models import CreateTripPayload, Itinerary
from .prompts import (
    DAY_PLANNER_SYSTEM,
    EVALUATOR_SYSTEM,
    FAST_TRIP_DRAFT_SYSTEM,
    INTERPRETER_SYSTEM,
    SKELETON_SYSTEM,
    TRIP_DRAFT_SYSTEM,
    day_planner_user,
    evaluator_user,
    fast_trip_draft_user,
    interpreter_user,
    skeleton_user,
    trip_draft_user,
)


TEST_MODEL = "deepseek-v4-flash"


class GenerationTestState(TypedDict, total=False):
    trip_id: str
    payload: CreateTripPayload
    planning_brief: dict[str, Any]
    skeleton: dict[str, Any]
    trip_draft: dict[str, Any]
    day_drafts: list[dict[str, Any]]
    itinerary: Itinerary
    evaluation: dict[str, Any]
    generation_events: list[dict[str, Any]]
    timings: dict[str, float]
    used_places: list[str]


def deepseek_json(
    messages: list[dict[str, str]],
    timeout: float = 45.0,
    *,
    generation_name: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    last_error: Exception | None = None
    retry_messages = messages
    for attempt in range(2):
        try:
            return raw_deepseek_json(
                retry_messages,
                timeout=timeout,
                generation_name=f"{generation_name}_attempt_{attempt + 1}",
                metadata={**(metadata or {}), "attempt": attempt + 1},
                model=TEST_MODEL,
            )
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            retry_messages = [
                *messages,
                {
                    "role": "user",
                    "content": "上一次输出不是合法 JSON。请严格只返回一个可被 json.loads 解析的 JSON object，不要 markdown，不要注释，不要多余文字。",
                },
            ]

    if last_error:
        raise last_error
    raise RuntimeError("LLM JSON generation failed")


def record_timing(state: GenerationTestState, key: str, started_at: float) -> None:
    timings = dict(state.get("timings") or {})
    timings[key] = round(time.perf_counter() - started_at, 2)
    state["timings"] = timings


def minutes_between(start_time: str, end_time: str) -> int:
    start_hour, start_minute = [int(part) for part in start_time.split(":")]
    end_hour, end_minute = [int(part) for part in end_time.split(":")]
    return max((end_hour * 60 + end_minute) - (start_hour * 60 + start_minute), 30)


def duration_label(minutes: int) -> str:
    hours = minutes // 60
    rest = minutes % 60
    if hours and rest:
        return f"{hours}h{rest}m"
    if hours:
        return f"{hours}h"
    return f"{rest}m"


def item_cost(raw_cost: Any, fallback: int = 0) -> int:
    if isinstance(raw_cost, int):
        return raw_cost if 0 <= raw_cost <= 2000 else fallback
    if isinstance(raw_cost, str):
        digits = "".join(char for char in raw_cost if char.isdigit())
        if digits:
            value = int(digits)
            return value if 0 <= value <= 2000 else fallback
    return fallback


def is_activity_item(item: dict[str, Any]) -> bool:
    title = str(item.get("title") or "")
    item_type = str(item.get("type") or "")
    text = f"{title}{item_type}"
    if any(keyword in text for keyword in ("早餐", "午餐", "晚餐", "用餐", "餐厅", "饭店")):
        return False
    if any(
        keyword in text
        for keyword in (
            "夜游",
            "夜市",
            "夜景",
            "街区",
            "步行街",
            "城市漫步",
            "景点",
            "博物馆",
            "遗址",
            "公园",
            "宫",
            "塔",
            "寺",
            "城墙",
            "古城",
            "文化",
            "体验",
        )
    ):
        return True
    return not item.get("mealType") and item.get("countsAsMajorPlace", True)


def weather_icon(desc: str) -> str:
    if "雨" in desc:
        return "🌧️"
    if "雪" in desc:
        return "❄️"
    if "阴" in desc:
        return "☁️"
    if "云" in desc:
        return "⛅"
    return "☀️"


def date_label(start_date: str, day: int) -> str:
    try:
        parsed = date.fromisoformat(start_date)
    except ValueError:
        return f"第 {day} 天"
    return (parsed + timedelta(days=day - 1)).isoformat()


def normalize_payload(payload: CreateTripPayload) -> dict[str, Any]:
    data = payload.model_dump()
    data["travelers"]["total"] = payload.travelers.total
    return data


def interpret_requirements(state: GenerationTestState) -> GenerationTestState:
    started_at = time.perf_counter()
    payload = state["payload"]
    pace_raw = payload.preferences.pace
    if pace_raw <= 35:
        pace_label = "relaxed"
        major_places_per_day = 2
    elif pace_raw >= 70:
        pace_label = "intensive"
        major_places_per_day = 4
    else:
        pace_label = "balanced"
        major_places_per_day = 3

    custom_text = payload.preferences.customText.strip()
    state["planning_brief"] = {
        "destination": payload.destination,
        "date_range": {"start": payload.startDate, "end": payload.endDate, "days": payload.days},
        "travelers": {
            "adults": payload.travelers.adults,
            "children": payload.travelers.children,
            "infants": payload.travelers.infants,
            "total": payload.travelers.total,
            "traveler_notes": [
                note
                for note in [
                    "有儿童，单日节奏需要更稳。" if payload.travelers.children else "",
                    "有婴幼儿，避免过长步行和过晚结束。" if payload.travelers.infants else "",
                ]
                if note
            ],
        },
        "pace": {"raw": pace_raw, "label": pace_label, "major_places_per_day": major_places_per_day},
        "interests": payload.preferences.interests,
        "transport": payload.preferences.transport,
        "accommodation": payload.preferences.accommodation,
        "budget": payload.budget.model_dump(),
        "hard_constraints": [],
        "soft_preferences": [custom_text] if custom_text else [],
        "must_visit": [],
        "avoid": [],
        "meal_preferences": [custom_text] if any(word in custom_text for word in ("吃", "美食", "餐", "小吃")) else [],
        "time_constraints": [custom_text] if any(word in custom_text for word in ("不要太赶", "休息", "早", "晚")) else [],
        "assumptions": ["快速生成模式：先生成可预览行程，后续后台补全 POI、路线、天气和图片。"],
    }
    record_timing(state, "interpret_requirements", started_at)
    return state


def plan_trip_skeleton(state: GenerationTestState) -> GenerationTestState:
    started_at = time.perf_counter()
    result = deepseek_json(
        [
            {"role": "system", "content": SKELETON_SYSTEM},
            {"role": "user", "content": skeleton_user(state["planning_brief"])},
        ],
        generation_name="test_trip_skeleton_planner",
        metadata={"trip_id": state["trip_id"]},
    )
    state["skeleton"] = result
    record_timing(state, "plan_trip_skeleton", started_at)
    return state


def plan_trip_draft(state: GenerationTestState) -> GenerationTestState:
    started_at = time.perf_counter()
    result = deepseek_json(
        [
            {"role": "system", "content": FAST_TRIP_DRAFT_SYSTEM},
            {"role": "user", "content": fast_trip_draft_user(state["planning_brief"])},
        ],
        generation_name="test_trip_draft_planner",
        metadata={"trip_id": state["trip_id"], "model": TEST_MODEL},
        timeout=75,
    )
    state["trip_draft"] = result
    state["day_drafts"] = list(result.get("days") or [])
    record_timing(state, "plan_trip_draft", started_at)
    return state


def plan_days(state: GenerationTestState) -> GenerationTestState:
    started_at = time.perf_counter()
    skeleton_days = state["skeleton"].get("days") or []
    used_places: list[str] = []
    drafts: list[dict[str, Any]] = []

    for index, skeleton_day in enumerate(skeleton_days):
        future_keywords: list[str] = []
        for future_day in skeleton_days[index + 1 :]:
            future_keywords.extend(future_day.get("candidate_keywords") or [])

        draft = deepseek_json(
            [
                {"role": "system", "content": DAY_PLANNER_SYSTEM},
                {
                    "role": "user",
                    "content": day_planner_user(
                        state["planning_brief"],
                        skeleton_day,
                        used_places,
                        future_keywords[:20],
                    ),
                },
            ],
            generation_name=f"test_day_{skeleton_day.get('day', index + 1)}_planner",
            metadata={"trip_id": state["trip_id"], "day": skeleton_day.get("day", index + 1)},
            timeout=60,
        )
        drafts.append(draft)
        for item in draft.get("items", []):
            if item.get("countsAsMajorPlace", True) and not item.get("mealType"):
                used_places.append(str(item.get("title") or ""))

    state["day_drafts"] = drafts
    state["used_places"] = used_places
    record_timing(state, "plan_days", started_at)
    return state


def resolve_item_with_amap(item: dict[str, Any], destination: str) -> dict[str, Any]:
    keywords = [str(item.get("title") or ""), *[str(keyword) for keyword in item.get("searchKeywords", [])]]
    for keyword in [keyword for index, keyword in enumerate(keywords) if keyword and keyword not in keywords[:index]]:
        try:
            pois = search_pois(keyword, destination, limit=8)
        except (AmapUnavailableError, ValueError):
            pois = []
        if not pois:
            continue

        poi = next((candidate for candidate in pois if not is_bad_poi_match(item, candidate)), pois[0])
        item["title"] = poi.name
        item["address"] = poi.address
        item["location"] = {"lat": poi.lat, "lng": poi.lng}
        item["poiId"] = poi.id
        item["source"] = "amap"
        item["imageUrl"] = poi.image_url
        if poi.cost:
            item["cost"] = item_cost(poi.cost, item_cost(item.get("cost"), 0))
        return item

    item["source"] = "llm_unverified"
    item["poiId"] = None
    item["location"] = None
    item["imageUrl"] = None
    return item


def is_bad_poi_match(item: dict[str, Any], poi: Any) -> bool:
    item_title = str(item.get("title") or "")
    poi_name = str(getattr(poi, "name", "") or "")
    poi_address = str(getattr(poi, "address", "") or "")
    candidate_text = f"{poi_name}{poi_address}"
    unavailable_keywords = ("暂停开放", "暂停营业", "停业", "关闭", "装修", "已关闭")
    if any(keyword in candidate_text for keyword in unavailable_keywords):
        return True
    blocked_types = (
        "酒店",
        "宾馆",
        "客栈",
        "旅馆",
        "公寓",
        "民宿",
        "停车场",
        "厕所",
        "卫生间",
        "公司",
        "便利店",
        "公交站",
        "地铁站",
        "站)",
    )
    if not any(word in item_title for word in blocked_types) and any(word in candidate_text for word in blocked_types):
        return True
    if item_title and item_title not in poi_name and len(item_title) >= 3:
        if any(keyword in item_title for keyword in ("街", "巷", "涌", "夜市", "步行街")) and not any(
            keyword in candidate_text for keyword in ("街", "巷", "涌", "夜市", "步行街")
        ):
            return True
        strong_tokens = [token for token in ("博物馆", "城墙", "宫", "塔", "寺", "街", "园", "山", "湖", "剧院", "遗址") if token in item_title]
        if strong_tokens and not any(token in poi_name for token in strong_tokens):
            return True
    return False


def normalize_meal_suggestions(raw: dict[str, Any] | None, items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    raw = raw if isinstance(raw, dict) else {}
    first_place = items[0]["title"] if items else None
    midday_place = items[min(len(items) - 1, 1)]["title"] if items else first_place
    last_place = items[-1]["title"] if items else None
    defaults = {
        "breakfast": {
            "time": "08:30",
            "area": "酒店附近",
            "suggestion": "酒店附近简餐，控制早晨通勤时间。",
            "nearbyPlace": first_place,
            "reason": "先保证体力和出发效率。",
        },
        "lunch": {
            "time": "12:00",
            "area": "上午活动附近",
            "suggestion": "选择上午活动附近的本地餐饮，减少折返。",
            "nearbyPlace": midday_place,
            "reason": "衔接上午和下午行程。",
        },
        "dinner": {
            "time": "18:00",
            "area": "下午结束区域附近",
            "suggestion": "选择下午结束区域附近的本地特色餐饮。",
            "nearbyPlace": last_place,
            "reason": "晚餐后可直接休息或安排轻量夜游。",
        },
    }

    normalized: dict[str, dict[str, Any]] = {}
    for meal, fallback in defaults.items():
        item = raw.get(meal) if isinstance(raw.get(meal), dict) else {}
        normalized[meal] = {
            "time": str(item.get("time") or fallback["time"]),
            "area": str(item.get("area") or fallback["area"]),
            "suggestion": str(item.get("suggestion") or fallback["suggestion"]),
            "nearbyPlace": item.get("nearbyPlace") or fallback["nearbyPlace"],
            "reason": str(item.get("reason") or fallback["reason"]),
        }
    return normalized


def meal_budget(meal_suggestions: dict[str, dict[str, Any]]) -> int:
    total = 0
    for meal, suggestion in meal_suggestions.items():
        text = f"{suggestion.get('area', '')}{suggestion.get('suggestion', '')}"
        if meal == "breakfast":
            total += 30
        elif any(keyword in text for keyword in ("特色", "小吃街", "商圈", "夜市", "回民街", "永兴坊")):
            total += 100
        else:
            total += 80
    return total


def route_for_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    located = [item for item in items if item.get("location")]
    if len(located) < 2:
        return {"distanceKm": 0, "walkKm": 0, "transitKm": 0, "durationLabel": "待规划"}

    total_km = 0.0
    total_minutes = 0
    for origin, destination in zip(located, located[1:]):
        try:
            route = driving_route(origin["location"], destination["location"])
        except (AmapUnavailableError, ValueError):
            route = None
        if not route:
            continue
        total_km += route.distance_km
        total_minutes += route.duration_minutes

    total_km = round(total_km, 1)
    walk_km = round(min(total_km * 0.25, total_km), 1)
    transit_km = round(max(total_km - walk_km, 0), 1)
    return {
        "distanceKm": total_km,
        "walkKm": walk_km,
        "transitKm": transit_km,
        "durationLabel": duration_label(total_minutes) if total_minutes else "待规划",
    }


def build_day_plan(
    state: GenerationTestState,
    draft: dict[str, Any],
    weather: Any,
    generation_status: str,
) -> dict[str, Any]:
    payload = state["payload"]
    day_number = int(draft.get("day") or 1)
    resolved_items: list[dict[str, Any]] = []
    raw_items = [item for item in draft.get("items", []) if is_activity_item(item)]
    for index, raw_item in enumerate(raw_items, start=1):
        item = dict(raw_item)
        item.pop("slot", None)
        item.pop("searchKeywords", None)
        item = resolve_item_with_amap(item, payload.destination)
        start_time = str(item.get("startTime") or "09:00")
        end_time = str(item.get("endTime") or "10:30")
        resolved_items.append(
            {
                "id": f"{state['trip_id']}_d{day_number}_{index}_{uuid4().hex[:4]}",
                "startTime": start_time,
                "endTime": end_time,
                "title": str(item.get("title") or "待定安排"),
                "type": str(item.get("type") or "城市体验"),
                "durationLabel": str(item.get("durationLabel") or duration_label(minutes_between(start_time, end_time))),
                "cost": item_cost(item.get("cost"), 0),
                "reason": str(item.get("reason") or ""),
                "transitFromPrev": item.get("transitFromPrev"),
                "address": item.get("address"),
                "location": item.get("location"),
                "poiId": item.get("poiId"),
                "source": item.get("source"),
                "imageUrl": item.get("imageUrl"),
                "mealType": None,
                "countsAsMajorPlace": True,
            }
        )

    route = route_for_items(resolved_items)
    ticket_budget = sum(item["cost"] for item in resolved_items if item["countsAsMajorPlace"] and not item.get("mealType"))
    meals = normalize_meal_suggestions(draft.get("mealSuggestions"), resolved_items)
    weather_desc = weather.desc if weather else "待查询"
    return {
        "day": day_number,
        "date": date_label(payload.startDate, day_number),
        "title": str(draft.get("title") or f"{payload.destination} Day {day_number}"),
        "generationStatus": generation_status,
        "weather": {
            "icon": weather_icon(weather_desc),
            "desc": weather_desc,
            "range": weather.range if weather else "--",
            "tip": weather.tip if weather else "天气数据待接入或查询失败，出行前建议确认。",
        },
        "mealSuggestions": meals,
        "budget": {"交通": 0, "餐饮": meal_budget(meals), "门票": ticket_budget, "其他": 0},
        "route": route,
        "items": resolved_items,
    }


def generate_days_incrementally(state: GenerationTestState) -> GenerationTestState:
    started_at = time.perf_counter()
    payload = state["payload"]
    skeleton_days = state["skeleton"].get("days") or []
    used_places: list[str] = []
    day_drafts: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    preview_days: list[dict[str, Any]] = []

    try:
        weather = weather_for_city(payload.destination)
    except (AmapUnavailableError, ValueError):
        weather = None

    for index, skeleton_day in enumerate(skeleton_days):
        day_started_at = time.perf_counter()
        day_number = int(skeleton_day.get("day") or index + 1)
        events.append({"day": day_number, "status": "generating", "message": f"第 {day_number} 天正在生成"})

        future_keywords: list[str] = []
        for future_day in skeleton_days[index + 1 :]:
            future_keywords.extend(future_day.get("candidate_keywords") or [])

        draft = deepseek_json(
            [
                {"role": "system", "content": DAY_PLANNER_SYSTEM},
                {
                    "role": "user",
                    "content": day_planner_user(
                        state["planning_brief"],
                        skeleton_day,
                        used_places,
                        future_keywords[:20],
                    ),
                },
            ],
            generation_name=f"test_incremental_day_{day_number}_planner",
            metadata={"trip_id": state["trip_id"], "day": day_number},
            timeout=60,
        )
        day_plan = build_day_plan(state, draft, weather, "preview")

        preview_days.append(day_plan)
        day_drafts.append(draft)
        for item in day_plan.get("items", []):
            if item.get("countsAsMajorPlace", True) and not item.get("mealType"):
                used_places.append(str(item.get("title") or ""))

        events.append(
            {
                "day": day_number,
                "status": "preview",
                "message": f"第 {day_number} 天已生成，可预览，暂不可编辑",
                "seconds": round(time.perf_counter() - day_started_at, 2),
            }
        )

    itinerary = Itinerary(
        tripId=state["trip_id"],
        destination=payload.destination,
        title=str(state["skeleton"].get("trip_title") or f"{payload.destination}{payload.days}日行程"),
        dateRange=f"{payload.startDate} - {payload.endDate}",
        travelers=payload.travelers.total,
        interests=list(state["planning_brief"].get("interests") or payload.preferences.interests),
        days=preview_days,
    )

    state["day_drafts"] = day_drafts
    state["used_places"] = used_places
    state["generation_events"] = events
    state["itinerary"] = itinerary
    record_timing(state, "generate_days_incrementally", started_at)
    return state


def enrich_trip_draft(state: GenerationTestState) -> GenerationTestState:
    started_at = time.perf_counter()
    payload = state["payload"]
    brief = state["planning_brief"]
    draft = state["trip_draft"]
    raw_days = draft.get("days") or []
    events: list[dict[str, Any]] = []
    days: list[dict[str, Any]] = []
    used_places: list[str] = []

    try:
        weather = weather_for_city(payload.destination)
    except (AmapUnavailableError, ValueError):
        weather = None

    for index, raw_day in enumerate(raw_days, start=1):
        day_started_at = time.perf_counter()
        day_number = int(raw_day.get("day") or index)
        events.append({"day": day_number, "status": "generating", "message": f"第 {day_number} 天正在补全 POI、天气和路线"})
        day_plan = build_day_plan(state, raw_day, weather, "preview")
        days.append(day_plan)
        used_places.extend(
            str(item.get("title") or "")
            for item in day_plan.get("items", [])
            if item.get("countsAsMajorPlace", True) and not item.get("mealType")
        )
        events.append(
            {
                "day": day_number,
                "status": "preview",
                "message": f"第 {day_number} 天已生成，可预览，暂不可编辑",
                "seconds": round(time.perf_counter() - day_started_at, 2),
            }
        )

    itinerary = Itinerary(
        tripId=state["trip_id"],
        destination=payload.destination,
        title=str(draft.get("trip_title") or f"{payload.destination}{payload.days}日行程"),
        dateRange=f"{payload.startDate} - {payload.endDate}",
        travelers=payload.travelers.total,
        interests=list(brief.get("interests") or payload.preferences.interests),
        days=days,
    )
    state["generation_events"] = events
    state["used_places"] = used_places
    state["itinerary"] = itinerary
    record_timing(state, "enrich_trip_draft", started_at)
    return state


def enrich_and_build_itinerary(state: GenerationTestState) -> GenerationTestState:
    started_at = time.perf_counter()
    payload = state["payload"]
    brief = state["planning_brief"]
    skeleton = state["skeleton"]

    try:
        weather = weather_for_city(payload.destination)
    except (AmapUnavailableError, ValueError):
        weather = None

    days: list[dict[str, Any]] = []
    for fallback_day, draft in enumerate(state["day_drafts"], start=1):
        day_number = int(draft.get("day") or fallback_day)
        resolved_items: list[dict[str, Any]] = []
        for index, raw_item in enumerate(draft.get("items", []), start=1):
            item = dict(raw_item)
            item.pop("searchKeywords", None)
            item = resolve_item_with_amap(item, payload.destination)
            start_time = str(item.get("startTime") or "09:00")
            end_time = str(item.get("endTime") or "10:30")
            resolved_items.append(
                {
                    "id": f"{state['trip_id']}_d{day_number}_{index}_{uuid4().hex[:4]}",
                    "startTime": start_time,
                    "endTime": end_time,
                    "title": str(item.get("title") or "待定安排"),
                    "type": str(item.get("type") or "城市体验"),
                    "durationLabel": str(item.get("durationLabel") or duration_label(minutes_between(start_time, end_time))),
                    "cost": item_cost(item.get("cost"), 0),
                    "reason": str(item.get("reason") or ""),
                    "transitFromPrev": item.get("transitFromPrev"),
                    "address": item.get("address"),
                    "location": item.get("location"),
                    "poiId": item.get("poiId"),
                    "source": item.get("source"),
                    "imageUrl": item.get("imageUrl"),
                    "mealType": item.get("mealType"),
                    "countsAsMajorPlace": bool(item.get("countsAsMajorPlace", True)),
                }
            )

        route = route_for_items(resolved_items)
        ticket_budget = sum(item["cost"] for item in resolved_items if item["countsAsMajorPlace"] and not item.get("mealType"))
        meal_budget = sum(item["cost"] for item in resolved_items if item.get("mealType"))
        weather_desc = weather.desc if weather else "待查询"
        days.append(
            {
                "day": day_number,
                "date": date_label(payload.startDate, day_number),
                "title": str(draft.get("title") or f"{payload.destination} Day {day_number}"),
                "weather": {
                    "icon": weather_icon(weather_desc),
                    "desc": weather_desc,
                    "range": weather.range if weather else "--",
                    "tip": weather.tip if weather else "天气数据待接入或查询失败，出行前建议确认。",
                },
                "budget": {"交通": 0, "餐饮": meal_budget, "门票": ticket_budget, "其他": 0},
                "route": route,
                "items": resolved_items,
            }
        )

    itinerary = Itinerary(
        tripId=state["trip_id"],
        destination=payload.destination,
        title=str(skeleton.get("trip_title") or f"{payload.destination}{payload.days}日行程"),
        dateRange=f"{payload.startDate} - {payload.endDate}",
        travelers=payload.travelers.total,
        interests=list(brief.get("interests") or payload.preferences.interests),
        days=days,
    )
    state["itinerary"] = itinerary
    record_timing(state, "enrich_and_build_itinerary", started_at)
    return state


def evaluate_itinerary(state: GenerationTestState) -> GenerationTestState:
    started_at = time.perf_counter()
    itinerary = state["itinerary"]
    brief = state["planning_brief"]
    expected_places = int(brief.get("pace", {}).get("major_places_per_day") or 3)
    issues: list[dict[str, Any]] = []
    seen: set[str] = set()

    for day in itinerary.days:
        major_items = [item for item in day.items if item.countsAsMajorPlace and not item.mealType]
        if abs(len(major_items) - expected_places) > 1:
            issues.append(
                {
                    "severity": "medium",
                    "day": day.day,
                    "message": f"当天主要地点数量为 {len(major_items)}，和节奏目标 {expected_places} 有偏差。",
                    "suggested_fix": "后续可由编辑 agent 添加或删减一个地点。",
                }
            )
        elif len(major_items) < expected_places:
            issues.append(
                {
                    "severity": "low",
                    "day": day.day,
                    "message": f"当天主要地点数量为 {len(major_items)}，略少于节奏目标 {expected_places}。",
                    "suggested_fix": "可增加一个同片区轻量景点、街区或夜游体验。",
                }
            )
        if not day.mealSuggestions:
            issues.append(
                {
                    "severity": "high",
                    "day": day.day,
                    "message": "缺少三餐建议。",
                    "suggested_fix": "补齐 breakfast/lunch/dinner。",
                }
            )
        meal_suggestions = day.mealSuggestions.model_dump() if day.mealSuggestions else {}
        if meal_suggestions:
            dinner = meal_suggestions.get("dinner") or {}
            dinner_text = f"{dinner.get('area', '')}{dinner.get('nearbyPlace', '')}{dinner.get('suggestion', '')}"
            item_titles = "".join(item.title for item in major_items)
            if any(keyword in dinner_text for keyword in ("不夜城", "夜市", "永兴坊", "回民街")) and not any(
                keyword in item_titles for keyword in ("不夜城", "夜市", "永兴坊", "回民街")
            ):
                issues.append(
                    {
                        "severity": "low",
                        "day": day.day,
                        "message": "晚餐区域提到适合夜游的街区，但 items 里没有对应轻量夜游安排。",
                        "suggested_fix": "把该街区加入夜间轻量体验，或把晚餐地点改到当天最后一个景点附近。",
                    }
                )
        if day.route.durationLabel == "待规划" and len(major_items) >= 2:
            issues.append(
                {
                    "severity": "medium",
                    "day": day.day,
                    "message": "路线还没有补全。",
                    "suggested_fix": "后台 enrichment 继续补坐标和路线。",
                }
            )
        for item in major_items:
            availability_text = f"{item.title}{item.address or ''}"
            if any(keyword in availability_text for keyword in ("暂停开放", "暂停营业", "停业", "关闭", "装修", "已关闭")):
                issues.append(
                    {
                        "severity": "high",
                        "day": day.day,
                        "message": f"景点可能不可用：{item.title}",
                        "suggested_fix": "替换为同片区开放状态更明确的景点。",
                    }
                )
            normalized = item.title.replace("·", "").replace("（", "(").split("(")[0]
            if normalized in seen:
                issues.append(
                    {
                        "severity": "medium",
                        "day": day.day,
                        "message": f"疑似重复景点：{item.title}",
                        "suggested_fix": "替换为同片区的新地点。",
                    }
                )
            seen.add(normalized)

    high_count = sum(1 for issue in issues if issue["severity"] == "high")
    medium_count = sum(1 for issue in issues if issue["severity"] == "medium")
    score = max(60, 100 - high_count * 18 - medium_count * 7 - (len(issues) - high_count - medium_count) * 3)
    state["evaluation"] = {
        "score": score,
        "passed": high_count == 0,
        "issues": issues,
        "summary": "规则评估：快速生成结果可先进入工作区，未完成的路线/POI/图片由后台继续补全。",
    }
    finalized_days = [day.model_copy(update={"generationStatus": "finalized"}) for day in state["itinerary"].days]
    state["itinerary"] = state["itinerary"].model_copy(update={"days": finalized_days})
    record_timing(state, "evaluate_itinerary", started_at)
    return state
