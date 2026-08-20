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
from typing import Any, get_args
from uuid import uuid4

from pydantic import ValidationError

from .amap import AmapPoi
from .generation import DEEPSEEK_MODEL, _post, _ticket_cost, destination_center, resolve_place
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
- 新增地点时 title 只写地点名称，不要加修饰语、不要编造地址坐标价格——
  系统会拿这个名字去高德核实，查不到就整条指令作废。写「李坑」而不是「李坑观景咖啡屋」。
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


def plan_edits(itinerary: Itinerary, message: str) -> tuple[list[EditOp], str]:
    """让模型把一句话翻成编辑操作。返回（操作列表，模型的话）。

    模型不调工具、只回文字是**正常路径**（澄清或说明做不到），此时操作列表为空。
    """
    body = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": EDIT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"当前行程：\n{json.dumps(slim_itinerary(itinerary), ensure_ascii=False)}"
                    f"\n\n我的要求：{message}"
                ),
            },
        ],
        "tools": [EDIT_TOOL],
        "temperature": 0.3,
    }

    # 实测单次 2.7~5.6 秒（生成是 60~135 秒，因为那要吐整份行程）。
    # 60 秒超时留足余量，同时避免卡死请求线程。
    data = _post(body, timeout=60)
    choice = data["choices"][0]["message"]
    calls = choice.get("tool_calls") or []
    if not calls:
        return [], (choice.get("content") or "").strip()

    try:
        args = json.loads(calls[0]["function"]["arguments"])
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        raise EditRejected("没看懂要改什么，请换个说法再试一次") from exc

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
            continue

        index = next((i for i, existing in enumerate(items) if existing.id == op.itemId), None)
        if index is None:
            # 模型编了个 id。实测 8 次调用 0 次编造，但样本小，校验必须做。
            raise EditRejected("没找到你说的那个条目，没有改动")

        if op.op == "delete":
            changes.append(_describe(op, items[index].title))
            items.pop(index)
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

        changes.append(_describe_update(op, current.title, patch))
        items[index] = current.model_copy(update=patch)
        touched.append(current.id)

    updated_days = [day.model_copy(update={"items": days[day.day]}) for day in itinerary.days]
    return itinerary.model_copy(update={"days": updated_days}), changes, touched
