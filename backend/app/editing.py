"""编辑行程：把一句自然语言翻译成编辑操作，校验、执行、生成回执。

放在这里而不是 repository 下，是为了不让仓储层反向依赖 agent 层——
`resolve_place` 属于生成链路，repository 只该管落库。

设计见 `docs/编辑Agent立项规划-v0.1.md` 3.5：模型新增地点时只给得出一个名字，
没有坐标、地址、图片。**必须去高德核实，核实不到就拒绝**，不能只存个名字。
实测模型会编出「汪口茶馆」这种不存在的地方，而真实地名（汪口/篁岭/江湾）全部命中。
放行未核实的条目，行程里就会出现一个地图上不存在的点——这正是项目一路砍掉
预算总额、公交系数所反对的东西。
"""

import json
import logging
import re
from typing import Any, get_args
from uuid import uuid4

from pydantic import ValidationError

from .amap import AmapPoi, driving_route, search_around, search_pois
from .generation import (
    DEEPSEEK_MODEL,
    MOVEMENT_TYPES,
    _post,
    _ticket_cost,
    destination_center,
    resolve_place,
)
from .models import (
    EditOp,
    InsertItineraryItemPayload,
    Itinerary,
    ItineraryItem,
    StopType,
    TimeSlot,
)
from .repository.itineraries import insert_position


logger = logging.getLogger(__name__)


class PlaceNotFoundError(Exception):
    """高德核实不到这个地名。带上原名，好让回执如实告诉用户查的是什么。"""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.name = name


# 模型不给时长时的兜底。宁可给个粗略值也不给 0——0 会让时间线看起来像瞬间完成。
DEFAULT_DURATION_BY_TYPE = {
    "food": 60,
    "sight": 90,
    "activity": 90,
    "rest": 30,
    "hotel": 0,
    "transfer": 30,
    "flight": 120,
    "train": 120,
}


def is_literal_match(name: str, poi: AmapPoi) -> bool:
    """要求高德结果的名称或地址里**字面出现**用户给的名字。

    比 resolve_place 自己的判据严得多，因为两者要的东西相反：生成路径要召回
    （名字大多真实，宁可宽松也别漏，核实率因此从 77% 提到接近 100%），
    insert 要准确（名字可能是模型编的，指错地方比拒绝更糟）。

    不调 MATCH_THRESHOLD 而是换判据，是因为实测分数分布里没有可用的阈值：
    真实地名 11 个全是 1.00，而编造的「李坑观景咖啡屋」拿到 0.95——它匹配到了
    「李坑」这个村子。0.95 来自反向包含（结果名 ⊂ 查询词），而这恰恰是
    「编造出的具体性」的特征：模型给了个更长的名字，我们只匹配到其中的地名部分，
    于是行程里出现一家实际不存在的咖啡屋，却带着李坑村的真实坐标。

    另有一条泄漏路径也被这道判据堵上：resolve_place 的第一层「精确查询」
    只校验地理范围、不校验相似度，而高德对任何关键词都会返回一个最相关结果——
    「婺源银河洗浴中心」因此拿到了「婺源县」的坐标。
    """
    query = name.replace(" ", "")
    target = f"{poi.name}{poi.address or ''}".replace(" ", "")
    return bool(query) and query in target


def build_verified_item(
    trip_id: str,
    day_number: int,
    destination: str,
    payload: InsertItineraryItemPayload,
    center: AmapPoi | None = None,
) -> ItineraryItem:
    """核实地名并构造条目。核实不到抛 PlaceNotFoundError。

    `title` 同时作为搜索名与展示名——立项文档里给模型的指令就是「新增地点时只给名称」，
    不像生成链路那样区分 name/label。
    """
    poi = resolve_place(payload.title, destination, destination, center or destination_center(destination))
    if not poi or not is_literal_match(payload.title, poi):
        raise PlaceNotFoundError(payload.title)

    duration = payload.durationMin
    if duration is None:
        duration = DEFAULT_DURATION_BY_TYPE.get(payload.stopType, 60)

    return ItineraryItem(
        id=f"{trip_id}_d{day_number}_{uuid4().hex[:6]}",
        title=payload.title,
        stopType=payload.stopType,
        timeSlot=payload.timeSlot,
        durationMin=duration,
        cost=_ticket_cost(poi),
        optional=False,
        bookRequired=False,
        verification="verified",
        reason=payload.reason,
        # 通勤耗时不在这里算：它取决于前后两个条目，插入后整天的顺序都变了。
        # 与其填一个当场算出、下次插入就失效的数字，不如留空。
        transitMinutes=None,
        transitMode=None,
        address=poi.address,
        location={"lat": poi.lat, "lng": poi.lng},
        poiId=poi.id,
        imageUrl=poi.image_url,
    )


# ── 对话编辑 ──────────────────────────────────────────────────────────
#
# 立项文档第 2 节：让模型输出**编辑操作**而不是重出整份行程。否决重出的决定性
# 理由不是时延，而是副作用——模型输出存在结构不稳定，用户只想换顿午饭，
# 第三天却被悄悄改了，这类改动没有任何提示。

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_places",
        "description": (
            "在高德地图上搜真实存在的地点。要新增餐厅、景点等地方时**必须先用它搜**，"
            "然后从返回结果里原样复制名称——不要凭记忆写店名。"
            "返回空列表表示那一带高德没有收录，这时如实告诉用户搜不到，不要编一个名字。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "day": {
                    "type": "integer",
                    "description": "第几天。用来定位搜索中心——按当天已有条目的坐标搜周边",
                },
                "category": {
                    "type": "string",
                    "enum": ["food", "sight", "activity", "hotel"],
                    "description": "要搜的品类",
                },
                "keyword": {
                    "type": "string",
                    "description": "可选。知道确切名字时填，例如「婺源博物馆」；找「附近有什么餐馆」时留空",
                },
            },
            "required": ["day", "category"],
        },
    },
}


EDIT_TOOL = {
    "type": "function",
    "function": {
        "name": "apply_edits",
        "description": "对当前行程执行一组编辑操作。只输出需要改动的部分，不要重出整份行程。",
        "parameters": {
            "type": "object",
            "properties": {
                "ops": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "op": {"type": "string", "enum": ["update", "delete", "insert"]},
                            "day": {"type": "integer", "description": "第几天，从 1 开始"},
                            "itemId": {
                                "type": "string",
                                "description": "update/delete 必填，须从行程里原样复制",
                            },
                            "title": {"type": "string", "description": "insert 必填：地点名称"},
                            "stopType": {"type": "string", "enum": list(get_args(StopType))},
                            "timeSlot": {"type": "string", "enum": list(get_args(TimeSlot))},
                            "durationMin": {"type": "integer"},
                            "cost": {"type": "integer"},
                            "reason": {"type": "string", "description": "为什么这样安排"},
                            "afterItemId": {
                                "type": "string",
                                "description": "insert 可选：插到这个条目之后；留空则按时段自动排位",
                            },
                        },
                        "required": ["op", "day"],
                    },
                },
                "reply": {"type": "string", "description": "给用户的一句话说明"},
            },
            "required": ["ops"],
        },
    },
}


# 这段措辞是实测选出来的，不是拍脑袋写的。立项文档 3.3：
# v1 写「指向不明时反问澄清」——四条指令全部反问、零改动，功能等于不可用；
# v2 改成下面这样——四条全部执行。差别只在 system prompt。
EDIT_SYSTEM_PROMPT = """你是行程编辑助手。用户会用自然语言提出修改要求，你负责把它翻译成编辑操作。

默认执行，不要反问。用户来这里是为了改行程，不是为了回答问题。多问一轮的代价
比选错一个条目的代价更高——选错了用户可以一键撤销。

规则：
- 只调用 apply_edits 输出需要改动的部分，绝不重新输出整份行程。
- itemId 必须从下面给出的行程里原样复制，不得自己编造或改写。
- 有多个条目符合时，按行程顺序选最合理的一个直接执行，并在 reply 里说明你选了哪个、
  以及「如果不是这个可以告诉我」。不要为此反问。
- 位置不明确时自己定：新增条目按时段插到合理位置即可，不要问用户插在第几个。
- 只有一种情况才反问：要求本身无法执行（例如要删的东西行程里根本没有）。
- **绝不把改动挪到别的天去。** 用户说第几天就是第几天；那天不存在就直接说明行程只有
  几天，不要「那我改第一天吧」——用户说 A 你改了 B，是最难被发现的错误。
- **新增或替换地点前必须先调 search_places 搜一次**，再从返回结果里**原样复制**名称。
  不要凭记忆写店名——你不知道当地有哪些店，编出来的名字高德查不到，整条指令会作废。
  传 day 与 category 即可，系统会按那一天的位置搜周边；知道确切名字时才填 keyword。
- 已经在行程里的著名景点可以直接引用，不必搜。
- search_places 返回空列表，说明那一带高德没有收录。**如实告诉用户「附近没搜到」**，
  不要退而求其次编一个名字——编出来的会被核实拦下，用户看到的是一句莫名其妙的报错。
- 不要编造地址、坐标或价格——这些由系统从高德取。
- reply 用一句话说明你做了什么，不要罗列选项。"""


def slim_itinerary(itinerary: Itinerary) -> dict[str, Any]:
    """给模型看的精简行程。

    地址、坐标、图片 URL、推荐理由对「改哪一条」没有帮助，却占了 3/4 体积
    （实测完整 2738 token → 精简 652 token，2 天行程）。7 天约 2300 token，
    整份塞进 prompt 也放得下，所以不需要做检索。
    """
    return {
        "days": [
            {
                "day": day.day,
                "date": day.date,
                "items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "stopType": item.stopType,
                        "timeSlot": item.timeSlot,
                        "durationMin": item.durationMin,
                    }
                    for item in day.items
                ],
            }
            for day in itinerary.days
        ]
    }


class EditRejected(Exception):
    """整条指令被拒。全成功或全不动——部分执行会留下用户无法理解的中间状态。"""


CHINESE_DIGITS = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
DAY_REFERENCE = re.compile(r"第\s*([0-9]+|[一二两三四五六七八九十]+)\s*天|\b[Dd]([1-9][0-9]?)\b")


def referenced_days(message: str) -> set[int]:
    """从用户的话里抠出他指名的是第几天。识别「第二天」「第3天」「D2」。"""
    days: set[int] = set()
    for arabic_or_chinese, d_form in DAY_REFERENCE.findall(message):
        raw = arabic_or_chinese or d_form
        if not raw:
            continue
        if raw.isdigit():
            days.add(int(raw))
        elif raw in CHINESE_DIGITS:
            days.add(CHINESE_DIGITS[raw])
        elif raw.startswith("十") and raw[1:] in CHINESE_DIGITS:  # 十一 ~ 十九
            days.add(10 + CHINESE_DIGITS[raw[1:]])

    return days


def guard_day_range(itinerary: Itinerary, message: str) -> None:
    """用户指名的天不存在时，直接拒绝，不交给模型去发挥。

    实测（天津 1 日行程）：用户说「第二天太赶了，删两个景点」，模型在回复里
    写着「行程目前只有一天」，**却仍然把两个景点删在了第一天**。它知道那天不存在，
    还是动了手——这是静默改指目标：用户说 A，系统对 B 执行了破坏性操作。

    `apply_ops` 里那道 `op.day not in days` 拦不住，因为模型吐的就是合法的 day=1。
    靠 prompt 约束也不可靠，模型会绕过去。所以在调模型之前先用代码挡掉，
    顺带省一次往返。
    """
    total = len(itinerary.days)
    out_of_range = sorted(day for day in referenced_days(message) if day < 1 or day > total)
    if out_of_range:
        named = "、".join(f"第 {day} 天" for day in out_of_range)
        raise EditRejected(f"这份行程只有 {total} 天，没有{named}。请确认要改哪一天。")


# 搜索最多来回两轮。一次搜不到合适的允许换个词再搜一次，再多就是在原地打转，
# 而每轮都要多花一次模型往返加一次高德查询。
MAX_SEARCH_ROUNDS = 2

# 给模型看的候选条数。多了会把 prompt 撑大且选择困难，少了容易没有合适的。
SEARCH_RESULT_LIMIT = 6


def day_anchor(itinerary: Itinerary, day_number: int) -> tuple[float, float] | None:
    """这一天的搜索中心：取当天第一个有坐标的条目。

    退回目的地中心而不是直接放弃——多日行程里某天可能一个坐标都没有。
    """
    for day in itinerary.days:
        if day.day != day_number:
            continue
        for item in day.items:
            location = item.location or {}
            if "lat" in location and "lng" in location:
                return location["lat"], location["lng"]

    center = destination_center(itinerary.destination)
    return (center.lat, center.lng) if center else None


def run_place_search(
    itinerary: Itinerary, day_number: int, category: str, keyword: str = ""
) -> list[dict[str, str]]:
    """替模型查高德，只回名称与地址。

    两条路：给了 keyword 就按名字查；没给就按当天坐标搜周边品类。后者是必需的——
    高德的文本检索匹配名称而非类别，实测「篁岭 餐厅」「江湾 美食」都是 0 条，
    「附近有什么餐馆」这类需求只能走周边检索。

    坐标、POI id 不给模型——它只需要挑一个名字，剩下的由 build_verified_item
    再查一次拿到。给多了徒增它编造坐标的机会。

    搜不到就返回空列表，让模型如实告诉用户，而不是逼它编一个名字。
    """
    pois = []
    try:
        if keyword:
            pois = search_pois(keyword, itinerary.destination, limit=SEARCH_RESULT_LIMIT)
        if not pois:
            anchor = day_anchor(itinerary, day_number)
            if anchor:
                pois = search_around(anchor[0], anchor[1], category, limit=SEARCH_RESULT_LIMIT)
    except Exception:
        logger.exception("对话编辑的地点搜索失败 day=%s category=%s keyword=%s", day_number, category, keyword)
        return []

    return [{"name": poi.name, "address": poi.address or ""} for poi in pois]


def plan_edits(itinerary: Itinerary, message: str) -> tuple[list[EditOp], str]:
    """让模型把一句话翻成编辑操作。返回（操作列表，模型的话）。

    模型可以先调 search_places 查真实地点再决定加什么——这一步是必要的：
    模型不知道当地有哪些餐馆，凭记忆写店名必然编造（实测它给出过「篁岭天街」
    「汪口茶馆」这类高德查不到的名字）。让它先看到真实候选，再原样复制名称。
    这与生成链路让模型先联网搜索是同一个模式：LLM 判断，高德供事实。

    模型不调工具、只回文字是**正常路径**（澄清或说明做不到），此时操作列表为空。
    """
    guard_day_range(itinerary, message)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": EDIT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"当前行程：\n{json.dumps(slim_itinerary(itinerary), ensure_ascii=False)}"
                f"\n\n我的要求：{message}"
            ),
        },
    ]

    choice: dict[str, Any] = {}
    args: dict[str, Any] | None = None

    for round_index in range(MAX_SEARCH_ROUNDS + 1):
        # 最后一轮收掉搜索工具，避免模型无限搜下去不给结果
        tools = [EDIT_TOOL] if round_index == MAX_SEARCH_ROUNDS else [EDIT_TOOL, SEARCH_TOOL]

        # 实测单次 3.9~6.4 秒（生成是 60~135 秒，因为那要吐整份行程）。
        # 60 秒超时留足余量，同时避免卡死请求线程。
        data = _post(
            {"model": DEEPSEEK_MODEL, "messages": messages, "tools": tools, "temperature": 0.3},
            timeout=60,
        )
        choice = data["choices"][0]["message"]
        calls = choice.get("tool_calls") or []
        if not calls:
            return [], (choice.get("content") or "").strip()

        search_calls = [c for c in calls if c.get("function", {}).get("name") == "search_places"]
        if not search_calls:
            try:
                args = json.loads(calls[0]["function"]["arguments"])
            except (json.JSONDecodeError, KeyError, IndexError) as exc:
                raise EditRejected("没看懂要改什么，请换个说法再试一次") from exc
            break

        messages.append(choice)
        for call in calls:
            name = call.get("function", {}).get("name")
            if name == "search_places":
                call_args = json.loads(call["function"]["arguments"])
                results = run_place_search(
                    itinerary,
                    int(call_args.get("day") or 1),
                    str(call_args.get("category") or "food"),
                    str(call_args.get("keyword") or ""),
                )
                logger.info("对话编辑搜索 %s → %d 条", call_args, len(results))
                content = json.dumps(results, ensure_ascii=False)
            else:
                # 同一轮里混着别的工具调用。必须每个 tool_call 都回一条，
                # 否则下一次请求会因缺少响应而被接口拒绝
                content = "[]"
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": content})

    if args is None:
        return [], (choice.get("content") or "").strip()

    ops = []
    for raw in args.get("ops") or []:
        try:
            ops.append(EditOp.model_validate(raw))
        except ValidationError as exc:
            # 越界枚举、缺 day 等都落在这里。整条拒绝而不是跳过这一条——
            # 跳过会让用户以为全做了。
            logger.info("模型给出的操作不合法：%s（%s）", raw, exc)
            raise EditRejected("我理解的改法不符合行程结构，没有改动") from exc

    return ops, str(args.get("reply") or "").strip()


FIELD_LABELS = (
    ("title", "标题"),
    ("timeSlot", "时段"),
    ("durationMin", "时长"),
    ("stopType", "类型"),
    ("cost", "费用"),
    ("reason", "说明"),
)


def _describe(op: EditOp, title: str) -> str:
    """回执文案。由代码依据实际执行的操作生成，不用模型的话——

    模型描述的是它以为自己做了什么，操作被拒时它照样会说「已改好」。
    """
    if op.op == "delete":
        return f"删除 D{op.day}「{title}」"
    return f"D{op.day} 新增「{title}」"


def _describe_update(op: EditOp, title: str, patch: dict[str, Any]) -> str:
    """只列**真正改了**的字段。patch 已剔除与原值相同的项。"""
    labels = [label for field, label in FIELD_LABELS if field in patch]
    return f"修改 D{op.day}「{title}」的" + "、".join(labels)


def recompute_day_transit(
    items: list[ItineraryItem], anchor: dict[str, float] | None = None
) -> list[ItineraryItem]:
    """重算一整天的段间通勤。

    结构一变，后面每条的 transitMinutes 就都过期了——往 D2 中间插一顿午饭，
    下一条算的还是「篁岭→江湾」，而实际起点已经变成那家餐厅。地图动线是按坐标
    实时画的会自动跟上，通勤耗时却是烤进数据里的，不重算就是一个看着确定的错数。

    语义与生成链路的 enrich_stops 保持一致：上一条是移动条目（航班/火车/转移）时
    不再叠加段间通勤——那段路已经计过时了。

    `anchor` 是前一晚的住宿坐标，用作当天第一条的起点——否则每天第一个景点的
    通勤会凭空消失（生成链路本来是算的，重算时漏掉就成了倒退）。
    """
    updated: list[ItineraryItem] = []
    previous_location: dict[str, float] | None = anchor
    previous_was_movement = False

    for item in items:
        is_movement = item.stopType in MOVEMENT_TYPES
        transit: int | None = None

        if previous_location is not None and not previous_was_movement and not is_movement:
            here, there = previous_location, item.location
            if here and there:
                try:
                    route = driving_route(here, there)
                    transit = route.duration_minutes if route else None
                except Exception:
                    # 路线查不到就留空。宁可不显示，也不留一个过期的数字
                    transit = None

        updated.append(item.model_copy(update={"transitMinutes": transit}))
        if item.location:
            previous_location = item.location
        previous_was_movement = is_movement

    return updated


def relocate_patch(title: str, destination: str, center: AmapPoi | None) -> dict[str, Any]:
    """标题换成了别的地方时，重新核实并给出该跟着变的字段。

    核实得到就换成新地点的坐标；核实不到就把位置信息**全部清空**并标为未核实——
    留着旧坐标比没有坐标更糟：条目看着已核实，地图却指向另一家店。
    """
    poi = resolve_place(title, destination, destination, center or destination_center(destination))
    if poi and is_literal_match(title, poi):
        return {
            "location": {"lat": poi.lat, "lng": poi.lng},
            "address": poi.address,
            "poiId": poi.id,
            "imageUrl": poi.image_url,
            "verification": "verified",
        }

    return {"location": None, "address": None, "poiId": None, "imageUrl": None, "verification": "unverified"}


def apply_ops(
    itinerary: Itinerary, ops: list[EditOp], center: AmapPoi | None = None
) -> tuple[Itinerary, list[str], list[str]]:
    """在内存里执行所有操作，返回（新行程，回执条目，被改动的条目 id）。

    **在内存里改完再一次性保存**，而不是逐个操作调仓储函数——那样会产生多份快照，
    而用户撤销时期望撤销的是「刚才那句话」，不是点三次（立项文档 5.2）。

    任一操作校验失败即抛 EditRejected，调用方不保存，行程完全不动。
    """
    days = {day.day: list(day.items) for day in itinerary.days}
    changes: list[str] = []
    touched: list[str] = []
    # 哪几天的顺序或位置变了，最后要重算整天的通勤
    restructured: set[int] = set()

    for op in ops:
        if op.day not in days:
            raise EditRejected(f"行程里没有第 {op.day} 天")

        items = days[op.day]

        if op.op == "insert":
            if not op.title or not op.timeSlot:
                raise EditRejected("新增地点缺少名称或时段，没有改动")

            payload = InsertItineraryItemPayload(
                title=op.title,
                timeSlot=op.timeSlot,
                stopType=op.stopType or "sight",
                durationMin=op.durationMin,
                reason=op.reason,
                afterItemId=op.afterItemId,
            )
            try:
                item = build_verified_item(itinerary.tripId, op.day, itinerary.destination, payload, center)
            except PlaceNotFoundError as exc:
                raise EditRejected(f"高德地图查不到「{exc.name}」，没有改动") from exc

            items.insert(insert_position(items, item, op.afterItemId), item)
            changes.append(_describe(op, item.title))
            touched.append(item.id)
            restructured.add(op.day)
            continue

        index = next((i for i, existing in enumerate(items) if existing.id == op.itemId), None)
        if index is None:
            # 模型编了个 id。实测 8 次调用 0 次编造，但样本小，校验必须做。
            raise EditRejected("没找到你说的那个条目，没有改动")

        if op.op == "delete":
            changes.append(_describe(op, items[index].title))
            items.pop(index)
            restructured.add(op.day)
            continue

        patch = op.model_dump(
            include={"title", "timeSlot", "durationMin", "stopType", "cost", "reason"},
            exclude_none=True,
        )
        # 只留真正变了的字段。模型常把「改成 1 小时」译成 durationMin=60，
        # 而原值本就是 60——照单全收会让回执声称改了、实际没动。
        current = items[index]
        patch = {field: value for field, value in patch.items() if getattr(current, field) != value}
        if not patch:
            continue

        # 改了标题就等于换了个地方，原来的坐标/地址/图片全都不再属于它。
        # 实测模型会用 update 把「花海餐厅」改名成「花田人家农家菜」——若不处理，
        # 条目会顶着新店名却带着旧店的经纬度，地图上指向错误位置。
        if "title" in patch and current.location:
            patch.update(relocate_patch(str(patch["title"]), itinerary.destination, center))
            restructured.add(op.day)  # 换了地方，前后两段路都变了

        changes.append(_describe_update(op, current.title, patch))
        items[index] = current.model_copy(update=patch)
        touched.append(current.id)

    # 结构变过的那几天重算通勤。只算变过的——每段都要打一次高德路线接口，
    # 没动过的天没有理由重来一遍
    stays = {day.day: day.stay for day in itinerary.days}
    for day_number in restructured:
        # 前一晚住哪儿，决定这一天从哪里出发
        previous_stay = stays.get(day_number - 1)
        days[day_number] = recompute_day_transit(
            days[day_number], previous_stay.location if previous_stay else None
        )

    updated_days = [day.model_copy(update={"items": days[day.day]}) for day in itinerary.days]
    return itinerary.model_copy(update={"days": updated_days}), changes, touched
