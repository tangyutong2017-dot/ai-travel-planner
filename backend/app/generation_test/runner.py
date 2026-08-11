from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from uuid import uuid4

from ..models import CreateTripPayload
from .graph import generation_test_graph


def default_payload() -> CreateTripPayload:
    return CreateTripPayload(
        destination="西安",
        startDate="2026-08-10",
        endDate="2026-08-14",
        days=5,
        travelers={"adults": 2, "children": 1, "infants": 0},
        budget={"min": 0, "max": 12000},
        preferences={
            "interests": ["文化历史", "美食探索", "自然风光"],
            "pace": 50,
            "transport": ["公共交通", "步行为主"],
            "accommodation": ["酒店"],
            "customText": "不要太赶，想吃本地特色；希望有历史文化，也要有适合孩子休息的安排。",
        },
    )


def load_payload(path: str | None) -> CreateTripPayload:
    if not path:
        return default_payload()

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return CreateTripPayload.model_validate(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the real-LLM/real-AMap generation test agent.")
    parser.add_argument("--payload", help="Path to a CreateTripPayload JSON file.")
    parser.add_argument("--out", default="/tmp/travel_planner_generation_test.json", help="Output JSON path.")
    args = parser.parse_args()

    payload = load_payload(args.payload)
    trip_id = f"test_{uuid4().hex[:8]}"
    started_at = time.perf_counter()
    result = generation_test_graph.invoke({"trip_id": trip_id, "payload": payload, "timings": {}})
    elapsed = round(time.perf_counter() - started_at, 2)

    output = {
        "tripId": trip_id,
        "elapsedSeconds": elapsed,
        "timings": result.get("timings", {}),
        "planningBrief": result.get("planning_brief"),
        "tripDraft": result.get("trip_draft"),
        "generationEvents": result.get("generation_events"),
        "evaluation": result.get("evaluation"),
        "itinerary": result["itinerary"].model_dump(),
    }
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": args.out, "elapsedSeconds": elapsed, "evaluation": output["evaluation"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
