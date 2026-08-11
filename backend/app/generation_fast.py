from __future__ import annotations

from .generation_test.graph import generation_test_graph
from .models import CreateTripPayload, Itinerary


def generate_fast_itinerary(trip_id: str, payload: CreateTripPayload) -> tuple[Itinerary, dict]:
    """Generate the MVP itinerary with the fast A+B workflow.

    The current production path uses:
    - rule-based interpreter
    - one fast LLM draft planner
    - AMap enrichment
    - rule-based evaluator
    """
    result = generation_test_graph.invoke({"trip_id": trip_id, "payload": payload, "timings": {}})
    return result["itinerary"], {
        "timings": result.get("timings", {}),
        "evaluation": result.get("evaluation", {}),
        "generationEvents": result.get("generation_events", []),
    }
