from .models import Itinerary


def edit_itinerary(
    itinerary: Itinerary,
    instruction: str,
    active_day: int | None = None,
) -> tuple[str, Itinerary]:
    """Temporary Editing Agent stub.

    The old Editing Agent has been removed while we redesign the agent
    workflow. Keeping this function preserves the FastAPI route contract so
    the frontend and backend can still run during the rebuild.
    """
    _ = instruction
    _ = active_day
    return "Editing Agent 正在重构中，当前未修改行程。", itinerary
