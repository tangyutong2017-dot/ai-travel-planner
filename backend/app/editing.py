"""新增行程条目：先核实，再构造。

放在这里而不是 repository 下，是为了不让仓储层反向依赖 agent 层——
`resolve_place` 属于生成链路，repository 只该管落库。

设计见 `docs/编辑Agent立项规划-v0.1.md` 3.5：模型新增地点时只给得出一个名字，
没有坐标、地址、图片。**必须去高德核实，核实不到就拒绝**，不能只存个名字。
实测模型会编出「汪口茶馆」这种不存在的地方，而真实地名（汪口/篁岭/江湾）全部命中。
放行未核实的条目，行程里就会出现一个地图上不存在的点——这正是项目一路砍掉
预算总额、公交系数所反对的东西。
"""

from uuid import uuid4

from .amap import AmapPoi
from .generation import _ticket_cost, destination_center, resolve_place
from .models import InsertItineraryItemPayload, ItineraryItem


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
