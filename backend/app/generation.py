"""Generation Agent：把用户输入变成一份可核实的行程。

分工（依据见 docs/Agent立项规划-v0.1.md 的六轮实测）：
  LLM   判断层  理解偏好、选点取舍、写主题与理由
  高德   事实层  地点是否存在、坐标、地址、门票、真实通勤、天气
  代码   几何层  时间轴推算、字段映射

LLM 不产出通勤时间与具体时刻——实测它系统性低估（最严重声称 5 分钟、实际 100 分钟），
且删掉这两个字段本身带来 4.5 倍提速。
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from difflib import SequenceMatcher
from typing import Any, Callable
from uuid import uuid4

from .amap import AmapPoi, driving_route, search_poi, search_pois, weather_forecast_for_city
from .llm import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from .models import CreateTripPayload, Itinerary, LocalTransport, StopType
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .websearch import WEB_SEARCH_TOOL, as_tool_result, is_websearch_configured, web_search

# 最多允许模型搜索几轮。实测 2 轮足够，留 3 轮余量防止它卡在搜索循环里。
MAX_SEARCH_ROUNDS = 3

# 每日起始时刻随节奏变化。若三档都用同样时长，「慢节奏」会算出每个景点待 4 小时。
DAY_START_BY_PACE = {"relaxed": (9, 30), "balanced": (8, 30), "packed": (8, 0)}

# 模型偶尔给出 schema 之外的类型，兜底到 sight 而不是让整次生成失败。
VALID_STOP_TYPES: set[str] = {"sight", "food", "activity", "rest", "flight", "train", "transfer", "hotel"}

# 高德里没有对应 POI 的类型，不必浪费查询
UNSEARCHABLE_TYPES = {"flight", "train", "transfer"}

logger = logging.getLogger(__name__)

ProgressFn = Callable[[int, str], None]


class GenerationError(RuntimeError):
    pass


# —— LLM ——


def _post(body: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        method="POST",
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
        data=json.dumps(body).encode(),
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def draft_plan(payload: CreateTripPayload, on_progress: ProgressFn) -> dict[str, Any]:
    """让模型产出行程骨架，过程中可调用 web_search。"""
    highest = 0

    def report(progress: int, message: str) -> None:
        # 进度只增不减。搜索报 30、下一轮起始报 27 会让进度条回退，看着像出错了
        nonlocal highest
        highest = max(highest, progress)
        on_progress(highest, message)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(payload)},
    ]
    tools = [WEB_SEARCH_TOOL] if is_websearch_configured() else None

    for round_index in range(MAX_SEARCH_ROUNDS + 1):
        # 单次调用要一分钟上下，进度条会长时间不动。把预期说出来，
        # 用户知道「还要一会儿」比看着 15% 卡住不动要好
        report(
            min(15 + round_index * 12, 50),
            "正在规划行程结构，大约需要 1 分钟" if round_index == 0 else "正在结合查到的信息调整安排",
        )
        body: dict[str, Any] = {"model": DEEPSEEK_MODEL, "messages": messages, "temperature": 0.4}
        if tools and round_index < MAX_SEARCH_ROUNDS:
            body["tools"] = tools
        else:
            # 最后一轮收掉工具并强制 JSON，避免模型无限搜索下去
            body["response_format"] = {"type": "json_object"}

        data = _post(body, timeout=300)
        message = data["choices"][0]["message"]
        calls = message.get("tool_calls")

        if not calls:
            return _parse_json(message.get("content") or "")

        messages.append(message)
        for call in calls:
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            queries = args.get("queries") or []
            report(28 + round_index * 12, f"正在查证：{'、'.join(q[:14] for q in queries[:2])}")
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": as_tool_result(web_search(queries)),
            })

    raise GenerationError("模型未能在限定轮数内给出行程")


def _parse_json(content: str) -> dict[str, Any]:
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end <= start:
        raise GenerationError("模型没有返回 JSON")
    try:
        return json.loads(content[start : end + 1])
    except json.JSONDecodeError as exc:
        raise GenerationError(f"模型返回的 JSON 无法解析：{exc}") from exc


# —— 高德核实 ——


def _name_variants(name: str, destination: str) -> list[str]:
    """地名检索的变体。

    实测失败样本：「纳木错扎西半岛」查不到，去掉目的地前缀后的「扎西半岛」命中。
    这类失败不是幻觉，是冗余前缀与用字偏差，值得多试一次。
    """
    variants = [name]
    for prefix in (destination, destination.rstrip("市州")):
        if prefix and name.startswith(prefix) and len(name) > len(prefix):
            variants.append(name[len(prefix) :])
    # 去掉括号内的补充说明
    for bracket in ("（", "(", "·", "—"):
        if bracket in name:
            variants.append(name.split(bracket)[0])

    # 头尾子串回退。实测「药王山照景台」（错字）与「纳木错扎西半岛」（冗余前缀）
    # 整串在高德返回 0 个候选，但「药王山」「扎西半岛」都能查到——
    # 核心地名往往在头部或尾部，中间的错字会废掉整串查询。
    core = name.split("（")[0].split("(")[0]
    for length in (4, 3):
        if len(core) > length + 1:
            variants.append(core[:length])
            variants.append(core[-length:])

    return [v for i, v in enumerate(variants) if v and len(v) >= 2 and v not in variants[:i]]


# 模糊匹配的采纳阈值。0.5 意味着候选名与查询词有一半以上重合，
# 低于此值宁可判为未核实——错误的坐标比没有坐标更糟。
MATCH_THRESHOLD = 0.5


def match_score(query: str, poi: AmapPoi) -> float:
    """查询词与候选 POI 的相似度。

    `amap.is_plausible_match` 只做单向包含（查询词 ⊂ 结果），
    漏掉了反向情形——实测「双廊古镇漫步（海街·观景平台）」查不到，
    因为结果「双廊古镇」是查询词的子串而非相反。这里双向都认。
    """
    q = query.replace(" ", "")
    target = f"{poi.name}{poi.address or ''}".replace(" ", "")
    if not q or not target:
        return 0.0

    # 双向包含直接算高分：一方完整出现在另一方里，基本可以确定是同一个地方
    if q in target:
        return 1.0
    if poi.name and poi.name.replace(" ", "") in q:
        return 0.95

    # 否则退回字符级相似度，与候选名（而非地址）比较，避免长地址稀释分数
    return SequenceMatcher(None, q, poi.name.replace(" ", "")).ratio()


def resolve_place(name: str, city: str, destination: str) -> AmapPoi | None:
    """核实一个地名。先精确查，失败再从候选里挑相似度最高的。"""
    for variant in _name_variants(name, destination):
        try:
            poi = search_poi(variant, city)
        except Exception:  # 网络异常不该中断整次生成
            poi = None
        if poi:
            return poi

    # 精确查询全部落空——取未过滤的候选做模糊比对
    for variant in _name_variants(name, destination):
        try:
            candidates = search_pois(variant, city, limit=5)
        except Exception:
            continue
        if not candidates:
            continue
        best = max(candidates, key=lambda c: match_score(variant, c))
        score = match_score(variant, best)
        if score >= MATCH_THRESHOLD:
            logger.info("模糊命中 %s → %s（相似度 %.2f）", name, best.name, score)
            return best

    return None


def resolve_all(stops: list[dict[str, Any]], city: str, destination: str) -> dict[str, AmapPoi]:
    """批量核实地名。并发——串行时几十个地点会明显拖慢。"""
    names = {
        (stop.get("name") or "").strip()
        for stop in stops
        if (stop.get("name") or "").strip() and stop.get("type") not in UNSEARCHABLE_TYPES
    }
    if not names:
        return {}

    with ThreadPoolExecutor(max_workers=8) as pool:
        pairs = list(pool.map(lambda n: (n, resolve_place(n, city, destination)), sorted(names)))

    # 记下查不到的原始地名。没有这行，核实失败时无从知道模型当时拿什么去搜的
    failed = [name for name, poi in pairs if not poi]
    if failed:
        logger.warning("高德未命中的地名：%s", "、".join(failed))

    return {name: poi for name, poi in pairs if poi}


def transit_minutes_between(a: AmapPoi, b: AmapPoi) -> int | None:
    try:
        route = driving_route({"lat": a.lat, "lng": a.lng}, {"lat": b.lat, "lng": b.lng})
    except Exception:
        return None
    return route.duration_minutes if route else None


# —— 时间轴 ——


# 本身即「移动」的条目：它们的时长就是通勤时间，不该再叠加一次段间通勤
MOVEMENT_TYPES = {"flight", "train", "transfer"}


def build_time_axis(
    stops: list[dict[str, Any]], resolved: dict[str, AmapPoi], pace: str
) -> list[dict[str, Any]]:
    """按停留时长与真实通勤推算每条的起始时刻。

    两条规则：
    1. transfer 夹在两个已核实地点之间时，用真实驾车时长替换模型估的时长——
       模型估的通勤系统性偏低，而这里恰好能拿到真值。
    2. 紧跟移动条目的下一条不再单独计通勤，否则同一段路会被算两次
       （实测：三河古镇返程既算了 transfer 的 90 分钟，又加了 47 分钟真实通勤）。
    """
    pois = [resolved.get((stop.get("name") or "").strip()) for stop in stops]
    durations = [max(int(stop.get("duration_min") or 60), 10) for stop in stops]

    # 规则 1：市内转移用真实驾车时长校正。跨城的 flight/train 无法用驾车路线衡量，保持原值
    for index, stop in enumerate(stops):
        if stop.get("type") != "transfer":
            continue
        before = next((pois[j] for j in range(index - 1, -1, -1) if pois[j]), None)
        after = next((pois[j] for j in range(index + 1, len(pois)) if pois[j]), None)
        if before and after:
            real = transit_minutes_between(before, after)
            if real:
                durations[index] = real

    hour, minute = DAY_START_BY_PACE.get(pace, (8, 30))
    cursor = hour * 60 + minute
    previous: AmapPoi | None = None
    previous_was_movement = False
    out: list[dict[str, Any]] = []

    for index, stop in enumerate(stops):
        poi = pois[index]
        is_movement = stop.get("type") in MOVEMENT_TYPES

        transit: int | None = None
        # 规则 2：上一条是移动条目的话，那段路已经计过时了
        if previous is not None and poi is not None and not previous_was_movement and not is_movement:
            transit = transit_minutes_between(previous, poi)
            if transit:
                cursor += transit

        out.append({**stop, "_startMinutes": cursor, "_transitMinutes": transit,
                    "_durationMin": durations[index]})
        cursor += durations[index]
        if poi is not None:
            previous = poi
        previous_was_movement = is_movement

    return out


def _hhmm(total_minutes: int) -> str:
    return f"{(total_minutes // 60) % 24:02d}:{total_minutes % 60:02d}"


# —— 映射 ——


def _stop_type(raw: Any) -> StopType:
    value = str(raw or "").strip()
    return value if value in VALID_STOP_TYPES else "sight"  # type: ignore[return-value]


def _transit_mode(preferred: list[LocalTransport]) -> LocalTransport:
    """通勤耗时统一按驾车计算（未接公交接口），但展示时尊重用户选择。"""
    return preferred[0] if preferred else "driving"


def to_itinerary(
    trip_id: str,
    payload: CreateTripPayload,
    plan: dict[str, Any],
    resolved: dict[str, AmapPoi],
    weather_by_city: dict[str, Any],
) -> Itinerary:
    mode = _transit_mode(payload.preferences.localTransport)
    days_out = []
    route: list[str] = []

    dates = day_dates(payload.startDate, len(plan.get("days") or []))

    for index, day in enumerate(plan.get("days") or [], start=1):
        stops = build_time_axis(
            day.get("stops") or [], resolved, payload.preferences.pace
        )
        city = str(day.get("city") or payload.destination)
        if city not in route:
            route.append(city)

        items = []
        for stop in stops:
            name = (stop.get("name") or "").strip()
            poi = resolved.get(name)
            label = str(stop.get("label") or name or "行程安排")
            items.append({
                "id": f"{trip_id}_d{index}_{uuid4().hex[:6]}",
                "title": label,
                "stopType": _stop_type(stop.get("type")),
                "startTime": _hhmm(stop["_startMinutes"]),
                "durationMin": stop["_durationMin"],
                "cost": _ticket_cost(poi),
                "optional": bool(stop.get("optional")),
                "bookRequired": "预约" in str(stop.get("note") or ""),
                # 有坐标即视为高德已核实；查不到的保留名称但不给坐标，UI 上可淡化处理
                "verification": "verified" if poi else "unverified",
                "reason": stop.get("reason") or None,
                "transitMinutes": stop.get("_transitMinutes"),
                "transitMode": mode if stop.get("_transitMinutes") else None,
                "address": poi.address if poi else None,
                "location": {"lat": poi.lat, "lng": poi.lng} if poi else None,
                "poiId": poi.id if poi else None,
                "imageUrl": poi.image_url if poi else None,
                "mealType": None,
            })

        iso_date = dates[index - 1] if index - 1 < len(dates) else ""
        weather = (weather_by_city.get(city) or {}).get(iso_date)
        days_out.append({
            "day": index,
            "date": iso_date or str(day.get("date") or f"第 {index} 天"),
            "city": city,
            "title": str(day.get("theme") or f"{city} Day {index}"),
            "weather": weather or NO_FORECAST,
            "stay": None,
            "items": items,
        })

    notes = [
        {"kind": "alert", "text": str(text)}
        for text in (plan.get("notes") or [])
        if str(text).strip()
    ]
    # 通勤一律按驾车估算，这一点必须让用户知道，不能默默把驾车时长当公交时长
    notes.append({"kind": "assumption", "text": "通勤耗时按驾车估算；票价与开放时间以现场公告为准。"})

    return Itinerary.model_validate({
        "tripId": trip_id,
        "title": str(plan.get("title") or payload.destination),
        "dateRange": f"{payload.startDate} - {payload.endDate}",
        "originCity": payload.originCity,
        "destination": payload.destination,
        "route": route or [payload.destination],
        "travelers": payload.travelers.model_dump(),
        "interests": payload.preferences.interests,
        "notes": notes,
        "bookings": [],
        "days": days_out,
    })


def _ticket_cost(poi: AmapPoi | None) -> int:
    """只采信高德给的数字票价。解析不出就记 0——不猜。"""
    if not poi or not poi.cost:
        return 0
    digits = "".join(char for char in str(poi.cost) if char.isdigit())
    return int(digits) if digits and len(digits) <= 4 else 0


def fetch_weather(cities: list[str]) -> dict[str, dict[str, Any]]:
    """按城市取预报，返回 {城市: {日期: 天气}}。"""

    def one(city: str):
        try:
            return city, weather_forecast_for_city(city)
        except Exception:
            return city, {}

    with ThreadPoolExecutor(max_workers=4) as pool:
        return {
            city: {
                day: {"icon": WEATHER_ICONS.get(_icon_key(w.desc), "☀️"), "desc": w.desc,
                      "range": w.range, "tip": w.tip}
                for day, w in forecast.items()
            }
            for city, forecast in pool.map(one, cities)
        }


# 高德只预报未来 3~4 天。出行日期更远时如实说明，不拿今天的天气冒充——
# 一份 9 月 1 日出发的行程显示 8 月 17 日的天气，比不显示更糟。
NO_FORECAST = {
    "icon": "📅",
    "desc": "暂无预报",
    "range": "--",
    "tip": "出行日期超出天气预报范围（约 3 天），临近出发时会自动更新。",
}


def _icon_key(desc: str) -> str:
    for key in WEATHER_ICONS:
        if key in desc:
            return key
    return ""


WEATHER_ICONS = {
    "雷": "⛈️", "雪": "❄️", "雨": "🌧️", "阴": "☁️", "云": "⛅",
    "雾": "🌫️", "霾": "🌫️", "风": "💨", "晴": "☀️",
}


def day_dates(start_date: str, days: int) -> list[str]:
    """从出发日推算每天的真实日期。不依赖模型给的 date 字段。"""
    try:
        start = date.fromisoformat(start_date)
    except ValueError:
        return [""] * days
    return [(start + timedelta(days=offset)).isoformat() for offset in range(days)]


# —— 入口 ——


def generate_itinerary(trip_id: str, payload: CreateTripPayload, on_progress: ProgressFn) -> Itinerary:
    started = time.perf_counter()

    on_progress(10, "正在理解你的偏好与出行约束")
    plan = draft_plan(payload, on_progress)

    all_stops = [stop for day in (plan.get("days") or []) for stop in (day.get("stops") or [])]
    on_progress(60, "正在核实地点信息")
    resolved = resolve_all(all_stops, payload.destination, payload.destination)

    cities = {str(day.get("city") or payload.destination) for day in (plan.get("days") or [])}
    on_progress(75, "正在查询路线与天气")
    weather = fetch_weather(sorted(cities))

    on_progress(90, "正在整理每日行程")
    itinerary = to_itinerary(trip_id, payload, plan, resolved, weather)

    elapsed = round(time.perf_counter() - started, 1)
    # 只统计「本该有 POI」的条目——航班、接驳、休息本就没有对应地点，
    # 算进分母会让核实率看起来很差
    # 分母只算「模型确实给了地名」的条目。航班接驳本就没有 POI；
    # 而「古城内酒店」「白族菜晚餐」这类模型有意留空的，是它拒绝编造场所名，
    # 算作失败等于惩罚诚实行为。
    searchable = [
        item
        for day in itinerary.days
        for item in day.items
        if item.poiId or item.verification == "verified" or item.stopType in ("sight", "activity")
    ]
    verified = sum(1 for item in searchable if item.verification == "verified")
    on_progress(96, f"生成完成，耗时 {elapsed}s，{verified}/{len(searchable)} 个地点已核实")
    return itinerary
