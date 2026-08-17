"""Generation Agent 的 prompt。

每条约束都对应一次实测失败，详见 docs/Agent立项规划-v0.1.md：
- name/label 分离并给正反例  → 地点存在性 1/15 提升到 6/6
- 不要通勤时间与具体时刻      → 模型系统性低估（最严重 5 分 vs 实际 100 分），
                              且删掉这两个字段带来 4.5 倍提速
- 节奏需量化                  → 否则模型把「慢节奏」理解成每天 6 站 11.5 小时
- 交通必须作为条目            → 两个模型都漏掉返程
"""

from __future__ import annotations

from .models import CreateTripPayload

PACE_GUIDE = {
    "relaxed": "慢节奏深度游，每天 2~3 个主要景点，不赶时间",
    "balanced": "适中节奏，每天 3~4 个主要景点",
    "packed": "紧凑高效，每天 4~5 个主要景点",
}

INTERCITY_LABELS = {"flight": "飞机", "train": "高铁或火车", "selfDrive": "自驾", "mixed": "混合方式"}

LOCAL_TRANSPORT_LABELS = {"walking": "步行为主", "transit": "公共交通", "driving": "驾车（自驾或打车）"}

PARTY_LABELS = {
    "solo": "独自一人",
    "couple": "情侣或夫妻",
    "friends": "朋友同行",
    "family": "家庭亲子",
    "multigenerational": "多代同游，有长辈随行",
}

COMFORT_LABELS = {"budget": "经济", "standard": "中等", "comfort": "舒适", "luxury": "豪华"}

ACTIVITY_LABELS = {
    "low": "体力有限，避免长距离步行、连续台阶与高强度徒步",
    "medium": "体力适中，可接受一般强度的步行与游览",
    "high": "体力好，能接受徒步、骑行等较高强度活动",
}

VISIT_LABELS = {
    "first": "第一次来这个目的地，经典必看的地方要覆盖",
    "returning": "来过这个目的地，希望避开已经打卡过的热门点，看些不一样的",
}


SYSTEM_PROMPT = """你是旅行行程规划师。

可以用 web_search 查地图数据给不了的信息：景区无障碍设施（电瓶车/索道/台阶）、
是否需预约、门票与老人儿童优惠、日出日落时间、季节性景观时段。
请把相关问题合并成一次调用，不要逐条搜。

【最重要的格式要求】每条行程要分开写两个字段：

  name  —— 纯地点名，必须能在地图 App 里原样搜到。
           只写地名本身，不要加括号、不要加说明、不要写"午餐""入住"这类动作。
           使用官方全称，注意用字准确。
           没有对应地点的条目（航班、接驳、自由活动）留空字符串。
  label —— 给用户看的展示文案，可以自由发挥。

  正确：  name="崇圣寺三塔文化旅游区"   label="崇圣寺三塔（园内电瓶车代步）"
          name="喜洲古镇"              label="喜洲午餐 · 破酥粑粑"
          name=""                     label="北京 → 大理 直飞航班"
  错误：  name="午餐（免辣）"           ← 不是地名
          name="大理古城酒店（入住）"     ← 混入了动作与括号
          name="大理古城漫游（人民路）"   ← 混入了说明

【住宿】每天给出 stay，说明当晚住在哪个**片区**：
- 只给片区或地标，如「大理古城南门一带」「合肥政务区天鹅湖附近」
- **不要推荐具体酒店名**——我们无法核实空房与价格，给了也是假精确
- 连续几天住同一片区就重复写同一个，不要为了变化而换宿
- 返程日当晚不住，stay 写 null

【城际交通时长】首日与末日必须包含城际交通条目，且 duration_min 要写实：
- 系统能用地图算出市内通勤，但**算不了航班与高铁**，所以这两项只能靠你估，请认真给
- 飞机：飞行时间 + 提前 2 小时到机场 + 落地取行李与进市区，通常合计 5~6 小时
- 高铁：车程 + 提前 30 分钟进站 + 出站进市区，例如上海到合肥车程约 2.5 小时，合计约 3.5 小时
- 不要凭感觉写 60 分钟这种明显偏短的值

其余要求：
- 同一天的地点应集中在同一片区，不要跨区往返
- 不要输出具体时刻，也不要估算通勤时间——这两项由系统用地图 API 计算
- note 写实用提示：是否需预约、门票优惠、无障碍设施、注意事项
- 价格与时刻类信息请注明「以现场为准」，因为网络信息可能过时"""


def build_user_prompt(payload: CreateTripPayload) -> str:
    """把结构化表单拼成自然语言 brief。

    规则字段直接翻译，customText 原样附上——由模型自行理解，
    这是它比规则强的地方。
    """
    travelers = payload.travelers
    people = [f"成人 {travelers.adults} 人"]
    if travelers.children:
        people.append(f"儿童 {travelers.children} 人")
    if travelers.infants:
        people.append(f"婴幼儿 {travelers.infants} 人")

    lines = [
        f"规划{payload.destination} {payload.days} 日行程"
        f"（{payload.startDate} 至 {payload.endDate}）。",
        f"出发城市：{payload.originCity}，"
        f"城际交通方式：{INTERCITY_LABELS.get(payload.intercityTransport, '不限')}。",
        f"同行人员：{'、'.join(people)}，{PARTY_LABELS.get(payload.travelParty, '')}。",
        f"节奏：{PACE_GUIDE.get(payload.preferences.pace, '适中')}。",
        f"体力：{ACTIVITY_LABELS.get(payload.preferences.activityLevel, '')}",
        f"档次偏好：{COMFORT_LABELS.get(payload.preferences.comfortLevel, '中等')}。",
        f"目的地内通勤方式："
        f"{'、'.join(LOCAL_TRANSPORT_LABELS.get(t, t) for t in payload.preferences.localTransport)}。",
        f"{VISIT_LABELS.get(payload.visitHistory, '')}",
    ]

    if payload.preferences.interests:
        lines.append(f"兴趣偏好：{'、'.join(payload.preferences.interests)}。")

    custom = (payload.preferences.customText or "").strip()
    if custom:
        lines.append(f"\n用户额外说明（请认真对待，这里往往是最重要的约束）：\n{custom}")

    lines.append(
        """
最终只输出 JSON：
{"title":"行程标题","days":[{"day":1,"theme":"当日主题","stops":[
 {"name":"纯地点名或空字符串","label":"展示文案",
  "type":"sight|food|activity|rest|flight|train|transfer|hotel",
  "duration_min":120,"reason":"为什么这样安排","note":"预约/优惠/无障碍等实用提示",
  "optional":false}],
  "stay":{"area":"住宿片区名","reason":"为什么住这里"}}],
 "notes":["整体提示，如安全、季节、证件等"]}"""
    )

    return "\n".join(line for line in lines if line.strip())
