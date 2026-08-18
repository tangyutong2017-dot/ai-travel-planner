"""占位行程与演示种子数据。

Generation Agent 重写完成后，这个模块整体删除——它存在的唯一目的是让
主流程在没有 agent 的情况下仍能端到端跑通。
"""

import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CreateTripPayload, Itinerary, Trip
from ..orm_models import TripRecord
from .itineraries import PLACEHOLDER_SOURCE, save_itinerary
from .naming import generate_trip_name


ENABLE_DEMO_SEED = os.getenv("ENABLE_DEMO_SEED", "").lower() in {"1", "true", "yes"}




def create_placeholder_itinerary(trip_id: str, payload: CreateTripPayload) -> Itinerary:
    """Generation Agent 未接入前的占位行程，用于保持主流程端到端可跑。

    刻意只产出最小骨架：一天一条占位条目，不编造餐饮与住宿。
    """
    interests = payload.preferences.interests or ["城市漫游", "美食探索"]

    return Itinerary(
        tripId=trip_id,
        title=generate_trip_name(payload),
        dateRange=f"{payload.startDate} - {payload.endDate}",
        originCity=payload.originCity,
        destination=payload.destination,
        route=[payload.destination],
        travelers=payload.travelers,
        interests=interests,
        notes=[
            {
                "kind": "alert",
                "text": "当前为占位行程，Generation Agent 重写完成后会替换为真实规划。",
            }
        ],
        days=[
            {
                "day": day,
                "date": f"第 {day} 天",
                "city": payload.destination,
                "title": f"{payload.destination} Day {day}",
                "weather": {"icon": "☀️", "desc": "待查询", "range": "--", "tip": "天气数据将在后端接入后实时更新"},
                "stay": None,
                "items": [
                    {
                        "id": f"{trip_id}_d{day}_seed",
                        "title": f"围绕「{interests[(day - 1) % len(interests)]}」生成核心安排",
                        "stopType": "sight",
                        "timeSlot": "morning",
                        "durationMin": 120,
                        "cost": 0,
                        "verification": PLACEHOLDER_SOURCE,
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
        save_itinerary(db, trip.id, create_seed_itinerary(trip), commit=False, snapshot_label=None)

    db.commit()


def create_seed_itinerary(trip: Trip) -> Itinerary:
    """演示种子行程（仅 ENABLE_DEMO_SEED=true 时使用）。

    刻意保持最小：每次输出结构变更都要同步维护假数据，内容越少代价越低。
    """
    return Itinerary(
        tripId=trip.id,
        title=trip.name,
        dateRange=f"{trip.date} 起",
        originCity="北京",
        destination=trip.dest,
        route=[trip.dest],
        travelers={"adults": 2, "children": 0, "infants": 0},
        interests=["城市漫游", "美食探索", "文化体验"],
        days=[
            {
                "day": day,
                "date": f"第 {day} 天",
                "city": trip.dest,
                "title": f"{trip.dest} Day {day}",
                "weather": {"icon": "☀️", "desc": "待查询", "range": "--", "tip": "真实天气将在后端接天气 API 后返回"},
                "stay": None,
                "items": [
                    {
                        "id": f"{trip.id}_d{day}_morning",
                        "title": f"{trip.dest} 核心区域探索",
                        "stopType": "sight",
                        "timeSlot": "morning",
                        "durationMin": 150,
                        "cost": 80,
                        "verification": PLACEHOLDER_SOURCE,
                        "reason": "用于前端工作区联调的后端种子数据",
                    },
                    {
                        "id": f"{trip.id}_d{day}_afternoon",
                        "title": "兴趣点组合行程",
                        "stopType": "activity",
                        "timeSlot": "afternoon",
                        "durationMin": 180,
                        "cost": 120,
                        "verification": PLACEHOLDER_SOURCE,
                        "transitMinutes": 20,
                        "transitMode": "transit",
                        "reason": "下一步由 LangGraph agent 替换为真实 POI 和路线",
                    },
                ],
            }
            for day in range(1, trip.days + 1)
        ],
    )
