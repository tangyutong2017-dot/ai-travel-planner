"""手写一份大理 3 日行程，用于检验新输出结构。

不是 agent 生成的——Generation Agent 尚未接入。这里手工编排，目的是让
stopType 枚举、stay、bookings、notes、optional、intensity 全部被真实数据覆盖，
以便在 UI 上看到「填满」的样子。

用户画像与向导一致：2 大 1 小、家庭、慢节奏、低体力、爸妈膝盖不好。
经纬度为手工填写的近似值，非高德返回，因此 verification 一律标 manual。
"""
import sys

sys.path.insert(0, "/Users/yutongtang/Desktop/Exercise/travel-planner/backend")

from app.db import SessionLocal
from app.models import CreateTripPayload, Itinerary
from app.repository import create_trip, save_itinerary

PAYLOAD = {
    "originCity": "北京",
    "destination": "云南大理",
    "startDate": "2026-09-01",
    "endDate": "2026-09-03",
    "days": 3,
    "intercityTransport": "flight",
    "travelers": {"adults": 2, "children": 1, "infants": 0},
    "travelParty": "multigenerational",
    "visitHistory": "first",
    "preferences": {
        "interests": ["自然风光", "美食探索", "文化历史"],
        "pace": "relaxed",
        "localTransport": ["walking", "driving"],
        "comfortLevel": "comfort",
        "activityLevel": "low",
        "customText": "爸妈膝盖不好，爬不了长台阶；孩子 8 岁；不吃辣；想看洱海日落",
    },
}

STAY = {
    "area": "大理古城南门一带",
    "location": {"lat": 25.6899, "lng": 100.1608},
    "reason": "三天行程重心都在古城与洱海西线，住南门可步行逛古城，去喜洲、三塔车程均在 30 分钟内",
}


def item(**kw):
    kw.setdefault("verification", "manual")
    kw.setdefault("cost", 0)
    return kw


DAYS = [
    {
        "day": 1,
        "date": "2026-09-01",
        "city": "云南大理",
        "title": "抵达古城，平路慢逛",
        "weather": {"icon": "⛅", "desc": "多云转阵雨", "range": "18-25℃", "tip": "九月为雨季尾声，午后易有阵雨，随身带伞"},
        "stay": STAY,
        "items": [
            item(
                id="dali_d1_1", title="北京首都 T3 → 大理荒草坝机场", stopType="flight",
                startTime="08:30", durationMin=240, cost=1180, intensity="low",
                address="大理荒草坝机场", location={"lat": 25.6494, "lng": 100.3193},
                bookRequired=True,
                reason="上午航班，落地后当天仍有完整下午可用",
            ),
            item(
                id="dali_d1_2", title="机场专车 → 大理古城", stopType="transfer",
                startTime="12:40", durationMin=45, cost=160, intensity="low",
                transitMinutes=45, transitMode="driving",
                reason="带老人小孩且有行李，比机场大巴省一次换乘",
            ),
            item(
                id="dali_d1_3", title="午餐 · 古城口白族菜", stopType="food",
                startTime="13:30", durationMin=60, cost=180, mealType="lunch",
                intensity="low", address="大理古城复兴路南段",
                reason="清淡不辣，有酸辣鱼可单独做不辣版本",
            ),
            item(
                id="dali_d1_4", title="入住 · 古城南门客栈", stopType="hotel",
                startTime="14:40", durationMin=40, intensity="low",
                address="大理古城南门附近", location=STAY["location"],
                transitMinutes=8, transitMode="walking",
                reason="先安顿行李再出门，避免拖着箱子逛街",
            ),
            item(
                id="dali_d1_5", title="大理古城 · 人民路与复兴路", stopType="sight",
                startTime="15:30", durationMin=120, intensity="low",
                address="大理市大理镇复兴路", location={"lat": 25.6944, "lng": 100.1614},
                transitMinutes=5, transitMode="walking",
                reason="全程平路无台阶，节奏自由，适合抵达当天恢复体力",
            ),
            item(
                id="dali_d1_6", title="南门城楼", stopType="sight",
                startTime="17:40", durationMin=40, intensity="mid", optional=True,
                address="大理古城南门", location={"lat": 25.6899, "lng": 100.1608},
                transitMinutes=6, transitMode="walking",
                reason="登城楼视野好，但需爬一段台阶——膝盖不适可在城楼下拍照后跳过",
            ),
            item(
                id="dali_d1_7", title="晚餐 · 古城内砂锅鱼", stopType="food",
                startTime="18:40", durationMin=80, cost=260, mealType="dinner",
                intensity="low", address="大理古城博爱路",
                transitMinutes=7, transitMode="walking",
                reason="砂锅鱼是大理家常菜代表，孩子也能吃",
            ),
        ],
    },
    {
        "day": 2,
        "date": "2026-09-02",
        "city": "云南大理",
        "title": "洱海西线与喜洲",
        "weather": {"icon": "☀️", "desc": "晴", "range": "17-26℃", "tip": "高原紫外线强，备防晒帽与墨镜"},
        "stay": STAY,
        "items": [
            item(
                id="dali_d2_1", title="早餐 · 客栈庭院", stopType="food",
                startTime="08:00", durationMin=40, cost=60, mealType="breakfast",
                intensity="low", address="大理古城南门客栈",
                reason="不赶时间，慢节奏的第一天完整行程",
            ),
            item(
                id="dali_d2_2", title="洱海生态廊道 · 才村段", stopType="activity",
                startTime="09:20", durationMin=90, intensity="low",
                address="大理市才村码头", location={"lat": 25.6850, "lng": 100.2150},
                transitMinutes=20, transitMode="driving",
                reason="全程平坦栈道，可租电瓶车代步，是看洱海最省力的方式",
            ),
            item(
                id="dali_d2_3", title="喜洲古镇 · 严家大院", stopType="sight",
                startTime="11:20", durationMin=100, cost=62, intensity="low",
                address="大理市喜洲镇四方街", location={"lat": 25.8582, "lng": 100.1425},
                transitMinutes=30, transitMode="driving", bookRequired=True,
                reason="白族三坊一照壁建筑代表，院内为平地，含三道茶表演可坐着看",
            ),
            item(
                id="dali_d2_4", title="午餐 · 喜洲破酥粑粑与白族菜", stopType="food",
                startTime="13:10", durationMin=70, cost=200, mealType="lunch",
                intensity="low", address="喜洲镇四方街周边",
                transitMinutes=5, transitMode="walking",
                reason="破酥粑粑是喜洲特产，甜咸两味孩子都爱吃",
            ),
            item(
                id="dali_d2_5", title="海舌生态公园", stopType="sight",
                startTime="14:40", durationMin=80, intensity="low",
                address="大理市喜洲镇海舌公园", location={"lat": 25.8480, "lng": 100.1650},
                transitMinutes=15, transitMode="driving",
                reason="伸入洱海的半岛，平路林荫道，人少好拍",
            ),
            item(
                id="dali_d2_6", title="洱海日落 · 才村码头", stopType="sight",
                startTime="18:00", durationMin=60, intensity="low",
                address="大理市才村码头", location={"lat": 25.6820, "lng": 100.2130},
                transitMinutes=35, transitMode="driving",
                reason="你提到想看洱海日落——九月日落约 19:10，此处西向视野开阔且可坐着等",
            ),
            item(
                id="dali_d2_7", title="晚餐 · 洱海边烤鱼", stopType="food",
                startTime="19:20", durationMin=80, cost=280, mealType="dinner",
                intensity="low", address="才村码头周边",
                transitMinutes=5, transitMode="walking",
                reason="可要求不加辣",
            ),
        ],
    },
    {
        "day": 3,
        "date": "2026-09-03",
        "city": "云南大理",
        "title": "崇圣寺三塔与返程",
        "weather": {"icon": "⛅", "desc": "多云", "range": "18-24℃", "tip": "返程日预留充足时间，机场距古城约 45 分钟车程"},
        "stay": None,
        "items": [
            item(
                id="dali_d3_1", title="早餐 · 古城米线", stopType="food",
                startTime="08:00", durationMin=40, cost=45, mealType="breakfast",
                intensity="low", address="大理古城人民路",
                reason="退房前先吃早餐，行李寄存在客栈",
            ),
            item(
                id="dali_d3_2", title="崇圣寺三塔文化旅游区", stopType="sight",
                startTime="09:10", durationMin=150, cost=75, intensity="mid",
                address="大理市银苍路", location={"lat": 25.7011, "lng": 100.1520},
                transitMinutes=15, transitMode="driving", bookRequired=True,
                reason="大理地标。景区纵深长且有连续上坡台阶，务必换乘园内电瓶车（35 元）直达上部",
            ),
            item(
                id="dali_d3_3", title="午餐 · 三塔附近农家菜", stopType="food",
                startTime="11:50", durationMin=70, cost=190, mealType="lunch",
                intensity="low", address="大理市银苍路",
                transitMinutes=8, transitMode="driving",
                reason="离景区近，饭后直接回古城取行李",
            ),
            item(
                id="dali_d3_4", title="苍山感通索道", stopType="activity",
                startTime="13:10", durationMin=120, cost=140, intensity="mid", optional=True,
                address="大理市苍山感通索道站", location={"lat": 25.6580, "lng": 100.1360},
                transitMinutes=20, transitMode="driving",
                reason="索道可坐着上山不爬台阶，但往返约 2 小时——赶飞机紧张时这是首个可砍项",
            ),
            item(
                id="dali_d3_5", title="取行李并前往机场", stopType="transfer",
                startTime="15:30", durationMin=60, cost=160, intensity="low",
                transitMinutes=45, transitMode="driving",
                reason="国内航班建议提前 90 分钟到机场",
            ),
            item(
                id="dali_d3_6", title="大理荒草坝机场 → 北京首都 T3", stopType="flight",
                startTime="18:20", durationMin=250, cost=1240, intensity="low",
                address="大理荒草坝机场", location={"lat": 25.6494, "lng": 100.3193},
                bookRequired=True,
                reason="傍晚航班，当天下午仍可安排一个景点",
            ),
        ],
    },
]

NOTES = [
    {"kind": "assumption", "text": "你提到爸妈膝盖不好，已避开苍山徒步与古城登高路线；崇圣寺三塔安排了园内电瓶车，南门城楼标为可选"},
    {"kind": "assumption", "text": "按不吃辣安排餐饮，砂锅鱼与烤鱼均可要求做不辣版本"},
    {"kind": "assumption", "text": "孩子 8 岁，每段步行控制在 30 分钟内，午后留出休息时段"},
    {"kind": "alert", "text": "九月为大理雨季尾声，午后阵雨概率高，建议随身带伞并把户外项目排在上午"},
    {"kind": "alert", "text": "大理海拔约 2000 米，通常无明显高反，但抵达首日不建议安排剧烈活动"},
    {"kind": "alert", "text": "洱海全线禁止下水游泳与私人游船，请勿轻信码头拉客"},
]

BOOKINGS = [
    {"itemId": "dali_d1_1", "channel": "航司官网 / 携程", "leadTimeDays": 30, "urgency": "high", "note": "九月为旺季尾声，提前一个月价格明显更低"},
    {"itemId": "dali_d3_6", "channel": "航司官网 / 携程", "leadTimeDays": 30, "urgency": "high", "note": "与去程一起订，往返通常更便宜"},
    {"itemId": "dali_d2_3", "channel": "喜洲严家大院官方公众号", "leadTimeDays": 1, "urgency": "mid", "note": "三道茶表演分场次，需选定场次购票"},
    {"itemId": "dali_d3_2", "channel": "崇圣寺三塔官方公众号", "leadTimeDays": 1, "urgency": "mid", "note": "门票 75 元不含园内电瓶车 35 元，需分开购买"},
]


def main() -> None:
    db = SessionLocal()
    try:
        payload = CreateTripPayload.model_validate(PAYLOAD)
        trip = create_trip(db, payload)

        itinerary = Itinerary.model_validate(
            {
                "tripId": trip.id,
                "title": "大理三日 · 洱海与古城慢游",
                "dateRange": f"{PAYLOAD['startDate']} - {PAYLOAD['endDate']}",
                "originCity": PAYLOAD["originCity"],
                "destination": PAYLOAD["destination"],
                "route": ["云南大理"],
                "travelers": PAYLOAD["travelers"],
                "interests": PAYLOAD["preferences"]["interests"],
                "notes": NOTES,
                "bookings": BOOKINGS,
                "days": DAYS,
            }
        )
        save_itinerary(db, trip.id, itinerary)
        print(f"已写入 tripId = {trip.id}")

        total_items = sum(len(d["items"]) for d in DAYS)
        types = sorted({i["stopType"] for d in DAYS for i in d["items"]})
        print(f"条目 {total_items} 个，覆盖 stopType: {types}")
        print(f"notes {len(NOTES)} 条，bookings {len(BOOKINGS)} 条")
    finally:
        db.close()


if __name__ == "__main__":
    main()
