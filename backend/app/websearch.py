"""Tavily 联网搜索封装。

存在的理由：高德给结构化事实（坐标、营业时间、门票），模型记忆给常识，
但两者都给不了「崇圣寺三塔有电瓶车不用爬坡」「9 月中旬稻田才金黄」这类
经验性与时效性信息——而它们恰恰决定行程对特定人群是否可行。

DeepSeek 不支持原生联网（tools 只接受 function 类型），因此包成 function tool。
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from .config import load_app_env

load_app_env()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_ENDPOINT = "https://api.tavily.com/search"

# —— 护栏 ——
# 联网 agent 最容易失控在「反复搜同一件事」和「把长正文灌爆上下文」上。
MAX_QUERIES_PER_CALL = 4
MAX_RESULTS_PER_QUERY = 3
MAX_CONTENT_CHARS = 800
CACHE_TTL_SECONDS = 24 * 3600


class WebSearchUnavailableError(RuntimeError):
    pass


def is_websearch_configured() -> bool:
    return bool(TAVILY_API_KEY)


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float


@dataclass
class QueryAnswer:
    """一次查询的结果。answer 是 Tavily 综合过的结论，比原始网页正文干净得多。"""

    answer: str
    results: list[SearchResult]


@dataclass
class _CacheEntry:
    payload: QueryAnswer
    stored_at: float = field(default_factory=time.time)

    @property
    def expired(self) -> bool:
        return time.time() - self.stored_at > CACHE_TTL_SECONDS


# 同一目的地的「生态廊道观光车票价」不该每次生成都重搜一遍。
_cache: dict[str, _CacheEntry] = {}


def _search_once(query: str, timeout: float) -> QueryAnswer:
    cached = _cache.get(query)
    if cached and not cached.expired:
        return cached.payload

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": MAX_RESULTS_PER_QUERY,
        # basic 比 advanced 快得多；旅游类查询不需要深度检索
        "search_depth": "basic",
        "include_answer": True,
    }
    request = urllib.request.Request(
        TAVILY_ENDPOINT,
        method="POST",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload).encode(),
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.load(response)

    results = [
        SearchResult(
            title=str(item.get("title") or ""),
            url=str(item.get("url") or ""),
            # 截断：Tavily 正文动辄数千字，三条就能把上下文顶满
            content=str(item.get("content") or "")[:MAX_CONTENT_CHARS],
            score=float(item.get("score") or 0.0),
        )
        for item in data.get("results", [])
    ]

    payload = QueryAnswer(answer=str(data.get("answer") or "")[:MAX_CONTENT_CHARS], results=results)
    _cache[query] = _CacheEntry(payload=payload)
    return payload


def web_search(queries: list[str], timeout: float = 20.0) -> dict[str, QueryAnswer]:
    """批量搜索。一次传多个 query，减少 LLM ↔ 工具的往返次数。

    单条查询失败不影响其余——联网本就不稳定，不该让一次超时毁掉整次生成。
    """
    if not TAVILY_API_KEY:
        raise WebSearchUnavailableError("TAVILY_API_KEY is not configured")

    picked = queries[:MAX_QUERIES_PER_CALL]

    def one(query: str) -> tuple[str, QueryAnswer]:
        try:
            return query, _search_once(query, timeout)
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
            return query, QueryAnswer(answer="", results=[])

    # 并发：串行时 8 条查询实测耗时 30.7 秒，而每条本身只要 3~4 秒
    with ThreadPoolExecutor(max_workers=max(len(picked), 1)) as pool:
        return dict(pool.map(one, picked))


def as_tool_result(results: dict[str, QueryAnswer]) -> str:
    """压成喂给 LLM 的紧凑文本。

    优先给 answer——它是综合过的结论；原始正文含大量网页导航噪音，
    只取前两条作为佐证，避免把上下文塞满垃圾。
    """
    blocks = []
    for query, payload in results.items():
        if not payload.answer and not payload.results:
            blocks.append(f"【{query}】未搜到结果")
            continue
        lines = [f"【{query}】"]
        if payload.answer:
            lines.append(payload.answer)
        lines.extend(f"· {item.title}：{item.content[:200]}" for item in payload.results[:2])
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


# 供 DeepSeek function calling 使用的工具声明
WEB_SEARCH_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "联网搜索实时信息。用于查询地图数据给不了的内容："
            "景区无障碍设施（电瓶车/索道/台阶）、是否需要预约、是否闭园、"
            "门票与老人儿童优惠、日出日落时间、季节性景观时段。"
            "可一次传多个问题，尽量合并以减少调用次数。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": f"搜索问题，最多 {MAX_QUERIES_PER_CALL} 条",
                }
            },
            "required": ["queries"],
        },
    },
}
