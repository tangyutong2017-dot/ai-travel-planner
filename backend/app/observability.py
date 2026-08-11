import os
from contextlib import contextmanager, nullcontext
from typing import Any, Iterator

from .config import load_app_env


load_app_env()

if os.getenv("LANGFUSE_BASE_URL") and not os.getenv("LANGFUSE_HOST"):
    os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_BASE_URL", "")

os.environ.setdefault("LANGFUSE_TIMEOUT", "30")

try:
    from langfuse import get_client
except Exception:  # pragma: no cover - optional dependency guard
    get_client = None  # type: ignore[assignment]


def is_langfuse_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY") and get_client)


def get_langfuse_client() -> Any | None:
    if not is_langfuse_enabled():
        return None

    try:
        return get_client()  # type: ignore[misc]
    except Exception:
        return None


def safe_update(observation: Any | None, **kwargs: Any) -> None:
    if observation is None:
        return

    payload = {key: value for key, value in kwargs.items() if value is not None}
    if not payload:
        return

    try:
        observation.update(**payload)
    except Exception:
        return


def flush_langfuse() -> None:
    client = get_langfuse_client()
    if client is None:
        return

    try:
        client.flush()
    except Exception:
        return


@contextmanager
def agent_trace(name: str, *, input: Any = None, metadata: dict[str, Any] | None = None) -> Iterator[Any | None]:
    client = get_langfuse_client()
    context = (
        client.start_as_current_span(name=name, input=input, metadata=metadata)
        if client is not None
        else nullcontext(None)
    )

    with context as span:
        try:
            yield span
        except Exception as exc:
            safe_update(span, level="ERROR", status_message=str(exc))
            raise
        finally:
            flush_langfuse()


@contextmanager
def agent_span(
    name: str,
    *,
    input: Any = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[Any | None]:
    client = get_langfuse_client()
    context = (
        client.start_as_current_span(name=name, input=input, metadata=metadata)
        if client is not None
        else nullcontext(None)
    )

    with context as span:
        try:
            yield span
        except Exception as exc:
            safe_update(span, level="ERROR", status_message=str(exc))
            raise


@contextmanager
def llm_generation(
    name: str,
    *,
    model: str,
    input: Any = None,
    metadata: dict[str, Any] | None = None,
    model_parameters: dict[str, Any] | None = None,
) -> Iterator[Any | None]:
    client = get_langfuse_client()
    context = (
        client.start_as_current_observation(
            name=name,
            as_type="generation",
            model=model,
            input=input,
            metadata=metadata,
            model_parameters=model_parameters,
        )
        if client is not None
        else nullcontext(None)
    )

    with context as generation:
        try:
            yield generation
        except Exception as exc:
            safe_update(generation, level="ERROR", status_message=str(exc))
            raise
