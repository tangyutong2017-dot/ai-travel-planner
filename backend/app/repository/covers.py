"""行程封面图：优先取行程内景点图，否则用地标关键词查高德。"""

import httpx

from ..amap import AmapUnavailableError, search_poi
from ..orm_models import TripRecord


def cover_url_from_days(days: list) -> str | None:
    for day in days:
        if not isinstance(day, dict):
            continue

        for item in day.get("items", []):
            if not isinstance(item, dict):
                continue

            image_url = item.get("imageUrl")
            if isinstance(image_url, str) and image_url.strip():
                return image_url

    return None


LANDMARK_KEYWORDS = [
    ("西藏", "布达拉宫"),
    ("拉萨", "布达拉宫"),
    ("云南大理", "大理古城"),
    ("大理", "大理古城"),
    ("北京", "故宫博物院"),
    ("浙江杭州", "西湖"),
    ("杭州", "西湖"),
    ("四川成都", "宽窄巷子"),
    ("成都", "宽窄巷子"),
    ("上海", "外滩"),
    ("广西桂林", "漓江"),
    ("桂林", "漓江"),
]


def landmark_keyword_for_destination(destination: str) -> str:
    for keyword, landmark in LANDMARK_KEYWORDS:
        if keyword in destination or destination in keyword:
            return landmark

    return destination


def cover_url_from_landmark(destination: str) -> str | None:
    try:
        poi = search_poi(landmark_keyword_for_destination(destination), destination)
    except (AmapUnavailableError, httpx.HTTPError, ValueError):
        return None

    return poi.image_url if poi else None


def ensure_cover_url(record: TripRecord) -> bool:
    if record.cover_url:
        return False

    if record.itinerary:
        record.cover_url = cover_url_from_days(record.itinerary.days_json)

    if not record.cover_url:
        record.cover_url = cover_url_from_landmark(record.dest)

    return bool(record.cover_url)
