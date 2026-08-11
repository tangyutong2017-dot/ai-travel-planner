"""行程数据访问层。

拆分自原先 620 行的 repository.py。这里重新导出全部公开名字，
因此 `from .repository import xxx` 的既有写法无需改动。
"""

from .naming import (  # noqa: F401
    generate_trip_name,
    make_trip_id,
    now_iso,
)
from .covers import (  # noqa: F401
    LANDMARK_KEYWORDS,
    cover_url_from_days,
    cover_url_from_landmark,
    ensure_cover_url,
    landmark_keyword_for_destination,
)
from .mappers import (  # noqa: F401
    count_major_itinerary_items,
    itinerary_from_record,
    job_from_record,
    trip_date_sort_value,
    trip_from_record,
)
from .placeholders import (  # noqa: F401
    ENABLE_DEMO_SEED,
    create_placeholder_itinerary,
    create_seed_itinerary,
    seed_initial_data,
)
from .trips import (  # noqa: F401
    create_trip,
    delete_trip,
    get_trip,
    get_trip_payload,
    list_trips,
    summarize_trips,
    update_trip_name,
)
from .itineraries import (  # noqa: F401
    PLACEHOLDER_SOURCE,
    delete_itinerary_item,
    is_placeholder_item,
    fill_missing_poi_data,
    get_itinerary,
    save_itinerary,
    update_itinerary_item,
)
from .jobs import (  # noqa: F401
    create_agent_job,
    get_agent_job,
    update_agent_job,
)

__all__ = [
    "ENABLE_DEMO_SEED",
    "LANDMARK_KEYWORDS",
    "PLACEHOLDER_SOURCE",
    "count_major_itinerary_items",
    "cover_url_from_days",
    "cover_url_from_landmark",
    "create_agent_job",
    "create_placeholder_itinerary",
    "create_seed_itinerary",
    "create_trip",
    "delete_itinerary_item",
    "delete_trip",
    "ensure_cover_url",
    "fill_missing_poi_data",
    "generate_trip_name",
    "get_agent_job",
    "get_itinerary",
    "get_trip",
    "get_trip_payload",
    "is_placeholder_item",
    "itinerary_from_record",
    "job_from_record",
    "landmark_keyword_for_destination",
    "list_trips",
    "make_trip_id",
    "now_iso",
    "save_itinerary",
    "seed_initial_data",
    "summarize_trips",
    "trip_date_sort_value",
    "trip_from_record",
    "update_agent_job",
    "update_itinerary_item",
    "update_trip_name",
]
