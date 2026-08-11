"""行程 ID 与展示名的生成规则。"""

from datetime import UTC, datetime
from uuid import uuid4

from ..models import CreateTripPayload


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def make_trip_id(destination: str) -> str:
    safe_destination = "".join(
        char for char in destination.strip().lower().replace(" ", "-")
        if char.isascii() and (char.isalnum() or char == "-")
    ).strip("-")
    return f"trip_{safe_destination or 'new'}_{uuid4().hex[:8]}"


PACE_WORDS = {"relaxed": "慢游", "balanced": "精选线", "packed": "深度快线"}


def generate_trip_name(payload: CreateTripPayload) -> str:
    interests = payload.preferences.interests or []
    pace_word = PACE_WORDS[payload.preferences.pace]

    theme_words = []
    for interest in interests:
        if "自然" in interest:
            theme_words.append("风光")
        elif "美食" in interest:
            theme_words.append("美食")
        elif "文化" in interest or "历史" in interest:
            theme_words.append("人文")
        elif "亲子" in interest:
            theme_words.append("亲子")
        elif "购物" in interest:
            theme_words.append("城市")

    unique_themes = []
    for word in theme_words:
        if word not in unique_themes:
            unique_themes.append(word)

    theme = "".join(unique_themes[:2]) or "旅行"
    return f"{payload.destination}{theme}{pace_word}"
