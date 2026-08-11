from __future__ import annotations

from langgraph.graph import END, StateGraph

from .nodes import (
    GenerationTestState,
    enrich_trip_draft,
    evaluate_itinerary,
    interpret_requirements,
    plan_trip_draft,
)


def build_generation_test_graph():
    graph = StateGraph(GenerationTestState)
    graph.add_node("interpret_requirements", interpret_requirements)
    graph.add_node("plan_trip_draft", plan_trip_draft)
    graph.add_node("enrich_trip_draft", enrich_trip_draft)
    graph.add_node("evaluate_itinerary", evaluate_itinerary)

    graph.set_entry_point("interpret_requirements")
    graph.add_edge("interpret_requirements", "plan_trip_draft")
    graph.add_edge("plan_trip_draft", "enrich_trip_draft")
    graph.add_edge("enrich_trip_draft", "evaluate_itinerary")
    graph.add_edge("evaluate_itinerary", END)
    return graph.compile()


generation_test_graph = build_generation_test_graph()
