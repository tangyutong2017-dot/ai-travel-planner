import json
import os
from typing import Any

import httpx

from .config import load_app_env
from .observability import llm_generation, safe_update


load_app_env()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")


class LLMUnavailableError(RuntimeError):
    pass


def is_deepseek_configured() -> bool:
    return bool(DEEPSEEK_API_KEY)


def extract_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("LLM response does not contain a JSON object")

    return json.loads(stripped[start : end + 1])


def deepseek_json(
    messages: list[dict[str, str]],
    timeout: float = 45.0,
    *,
    generation_name: str = "deepseek_json",
    metadata: dict[str, Any] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    if not DEEPSEEK_API_KEY:
        raise LLMUnavailableError("DEEPSEEK_API_KEY is not configured")

    model_name = model or DEEPSEEK_MODEL
    request_body = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    }

    with llm_generation(
        generation_name,
        model=model_name,
        input=messages,
        metadata=metadata,
        model_parameters={"temperature": 0.4, "response_format": "json_object"},
    ) as generation:
        response = httpx.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json=request_body,
            timeout=timeout,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            safe_update(
                generation,
                level="ERROR",
                status_message=f"DeepSeek API returned {response.status_code}: {response.text[:500]}",
                output={"status_code": response.status_code, "body": response.text[:1000]},
            )
            raise exc

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = extract_json_object(content)
        safe_update(generation, output={"content": content, "parsed": parsed}, usage_details=data.get("usage"))
        return parsed
