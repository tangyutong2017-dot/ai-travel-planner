import os
import time
from dataclasses import dataclass

import httpx

from .config import load_app_env


load_app_env()

AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")
AMAP_BASE_URL = "https://restapi.amap.com"
AMAP_REQUEST_INTERVAL_SECONDS = 0.25


class AmapUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class AmapPoi:
    id: str
    name: str
    address: str
    lat: float
    lng: float
    image_url: str | None = None
    poi_type: str | None = None
    city: str | None = None
    district: str | None = None
    rating: str | None = None
    cost: str | None = None
    open_time: str | None = None


@dataclass(frozen=True)
class AmapRoute:
    distance_km: float
    duration_minutes: int


@dataclass(frozen=True)
class AmapWeather:
    desc: str
    range: str
    tip: str


def is_amap_configured() -> bool:
    return bool(AMAP_API_KEY)


def is_plausible_match(keyword: str, city: str, name: str, address: str) -> bool:
    compact_keyword = keyword.replace(" ", "")
    compact_city = city.replace(" ", "")
    haystack = f"{name}{address}".replace(" ", "")
    city_tokens = [compact_city]

    for prefix in ("中国", "云南", "四川", "浙江", "江苏", "广东", "广西", "北京", "上海", "重庆", "天津"):
        if compact_city.startswith(prefix) and compact_city != prefix:
            city_tokens.append(compact_city.removeprefix(prefix))

    if compact_keyword and compact_keyword in haystack:
        return True

    place_keyword = compact_keyword
    for token in city_tokens:
        if token and place_keyword.startswith(token):
            place_keyword = place_keyword.removeprefix(token)
    place_keyword = place_keyword.strip()

    if len(place_keyword) >= 2:
        return place_keyword in haystack

    return any(token and token in haystack for token in city_tokens)


def keyword_variants(keyword: str) -> list[str]:
    compact = keyword.strip()
    suffixes = [
        "街区夜游",
        "夜游",
        "街区",
        "参观",
        "游览",
        "散步",
        "徒步",
        "文化体验",
        "美食探索",
        "自然风光",
        "城市漫步",
        "深度游",
        "半日游",
        "一日游",
        "体验",
        "漫步",
        "骑行",
        "游览",
        "观景",
        "打卡",
    ]
    variants = [compact]

    for separator in ("：", ":"):
        if separator in compact:
            parts = [part.strip() for part in compact.split(separator) if part.strip()]
            if len(parts) > 1:
                variants.extend(parts[1:])
                variants.extend(parts[:1])

    for separator in (" - ", " · ", "，", ","):
        if separator in compact:
            variants.extend(part.strip() for part in compact.split(separator) if part.strip())

    for connector in ("及", "和", "与", "+", "/"):
        current_variants = list(variants)
        for variant in current_variants:
            if connector in variant:
                variants.extend(part.strip() for part in variant.split(connector) if part.strip())

    for suffix in suffixes:
        for variant in list(variants):
            if variant.endswith(suffix):
                variants.append(variant[: -len(suffix)].strip(" ·-—：:，,"))

    return [variant for index, variant in enumerate(variants) if variant and variant not in variants[:index]]


def search_poi(keyword: str, city: str, timeout: float = 12.0) -> AmapPoi | None:
    if not AMAP_API_KEY:
        raise AmapUnavailableError("AMAP_API_KEY is not configured")

    pois = search_pois(keyword, city, limit=1, timeout=timeout)
    return pois[0] if pois else None


def search_pois(keyword: str, city: str, limit: int = 5, timeout: float = 12.0) -> list[AmapPoi]:
    if not AMAP_API_KEY:
        raise AmapUnavailableError("AMAP_API_KEY is not configured")

    results: list[AmapPoi] = []
    seen: set[str] = set()

    for keyword_variant in keyword_variants(keyword):
        for poi in search_pois_once(keyword_variant, city, limit=limit, timeout=timeout):
            dedupe_key = poi.id or f"{poi.name}:{poi.address}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            results.append(poi)
            if len(results) >= limit:
                return results

    return results


def search_poi_once(keyword: str, city: str, timeout: float = 12.0) -> AmapPoi | None:
    pois = search_pois_once(keyword, city, limit=1, timeout=timeout)
    return pois[0] if pois else None


def search_pois_once(keyword: str, city: str, limit: int = 5, timeout: float = 12.0) -> list[AmapPoi]:
    time.sleep(AMAP_REQUEST_INTERVAL_SECONDS)
    response = httpx.get(
        f"{AMAP_BASE_URL}/v5/place/text",
        params={
            "key": AMAP_API_KEY,
            "keywords": keyword,
            "region": city,
            "city_limit": "false",
            "show_fields": "business,photos",
            "page_size": min(max(limit, 1), 25),
        },
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "1":
        raise AmapUnavailableError(data.get("info", "Amap request failed"))

    pois = data.get("pois") or []
    if not pois:
        return []

    results: list[AmapPoi] = []
    for poi in pois:
        parsed = amap_poi_from_payload(poi, keyword)
        if not parsed:
            continue

        if not is_plausible_match(keyword, city, parsed.name, parsed.address):
            continue

        results.append(parsed)
        if len(results) >= limit:
            return results

    return results


def amap_poi_from_payload(poi: dict, fallback_name: str) -> AmapPoi | None:
    location = poi.get("location") or ""
    if "," not in location:
        return None

    lng_text, lat_text = location.split(",", maxsplit=1)
    address = poi.get("address")
    if isinstance(address, list):
        address = ""

    photos = poi.get("photos") or []
    image_url = None
    if photos and isinstance(photos, list):
        image_url = photos[0].get("url") if isinstance(photos[0], dict) else None

    business = poi.get("business") if isinstance(poi.get("business"), dict) else {}

    return AmapPoi(
        id=str(poi.get("id", "")),
        name=str(poi.get("name") or fallback_name),
        address=str(address or ""),
        lat=float(lat_text),
        lng=float(lng_text),
        image_url=image_url,
        poi_type=str(poi.get("type") or "") or None,
        city=str(poi.get("cityname") or "") or None,
        district=str(poi.get("adname") or "") or None,
        rating=str(business.get("rating") or "") or None,
        cost=str(business.get("cost") or "") or None,
        open_time=str(business.get("opentime_today") or business.get("opentime_week") or "") or None,
    )


def walking_route(origin: dict[str, float], destination: dict[str, float], timeout: float = 12.0) -> AmapRoute | None:
    if not AMAP_API_KEY:
        raise AmapUnavailableError("AMAP_API_KEY is not configured")

    time.sleep(AMAP_REQUEST_INTERVAL_SECONDS)
    response = httpx.get(
        f"{AMAP_BASE_URL}/v3/direction/walking",
        params={
            "key": AMAP_API_KEY,
            "origin": f"{origin['lng']},{origin['lat']}",
            "destination": f"{destination['lng']},{destination['lat']}",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "1":
        raise AmapUnavailableError(data.get("info", "Amap walking route failed"))

    paths = data.get("route", {}).get("paths") or []
    if not paths:
        return None

    path = paths[0]
    distance_km = round(float(path.get("distance", 0)) / 1000, 1)
    duration_minutes = max(1, round(float(path.get("duration", 0)) / 60))
    return AmapRoute(distance_km=distance_km, duration_minutes=duration_minutes)


def driving_route(origin: dict[str, float], destination: dict[str, float], timeout: float = 12.0) -> AmapRoute | None:
    if not AMAP_API_KEY:
        raise AmapUnavailableError("AMAP_API_KEY is not configured")

    time.sleep(AMAP_REQUEST_INTERVAL_SECONDS)
    response = httpx.get(
        f"{AMAP_BASE_URL}/v3/direction/driving",
        params={
            "key": AMAP_API_KEY,
            "origin": f"{origin['lng']},{origin['lat']}",
            "destination": f"{destination['lng']},{destination['lat']}",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "1":
        raise AmapUnavailableError(data.get("info", "Amap driving route failed"))

    paths = data.get("route", {}).get("paths") or []
    if not paths:
        return None

    path = paths[0]
    distance_km = round(float(path.get("distance", 0)) / 1000, 1)
    duration_minutes = max(1, round(float(path.get("duration", 0)) / 60))
    return AmapRoute(distance_km=distance_km, duration_minutes=duration_minutes)


def geocode_city(city: str, timeout: float = 12.0) -> str | None:
    if not AMAP_API_KEY:
        raise AmapUnavailableError("AMAP_API_KEY is not configured")

    time.sleep(AMAP_REQUEST_INTERVAL_SECONDS)
    response = httpx.get(
        f"{AMAP_BASE_URL}/v3/geocode/geo",
        params={"key": AMAP_API_KEY, "address": city},
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "1":
        raise AmapUnavailableError(data.get("info", "Amap geocode failed"))

    geocodes = data.get("geocodes") or []
    if not geocodes:
        return None

    return str(geocodes[0].get("adcode") or "") or None


def weather_for_city(city: str, timeout: float = 12.0) -> AmapWeather | None:
    """当日天气。保留给不关心具体日期的场景。"""
    forecast = weather_forecast_for_city(city, timeout=timeout)
    return next(iter(forecast.values()), None) if forecast else None


def weather_forecast_for_city(city: str, timeout: float = 12.0) -> dict[str, AmapWeather]:
    """按日期返回预报，键为 YYYY-MM-DD。

    高德只提供未来 3~4 天。出行日期超出范围时这里不会有对应键——
    调用方应如实告知「暂无预报」，而不是拿今天的天气顶上去。
    """
    adcode = geocode_city(city, timeout=timeout)
    if not adcode:
        return {}

    time.sleep(AMAP_REQUEST_INTERVAL_SECONDS)
    response = httpx.get(
        f"{AMAP_BASE_URL}/v3/weather/weatherInfo",
        params={"key": AMAP_API_KEY, "city": adcode, "extensions": "all"},
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("status") != "1":
        raise AmapUnavailableError(data.get("info", "Amap weather failed"))

    forecasts = data.get("forecasts") or []
    casts = forecasts[0].get("casts") if forecasts else []

    out: dict[str, AmapWeather] = {}
    for cast in casts or []:
        date = str(cast.get("date") or "").strip()
        if not date:
            continue
        day_weather = str(cast.get("dayweather") or "待查询")
        night_weather = str(cast.get("nightweather") or day_weather)
        day_temp = str(cast.get("daytemp") or "--")
        night_temp = str(cast.get("nighttemp") or "--")
        out[date] = AmapWeather(
            desc=day_weather if day_weather == night_weather else f"{day_weather}转{night_weather}",
            range=f"{night_temp}-{day_temp}°C",
            tip="天气来自高德预报，出行前建议再次确认。",
        )
    return out
