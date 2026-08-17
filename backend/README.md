# Travel Planner Backend

FastAPI backend for the travel planner web app.

## Run locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs:

```txt
http://127.0.0.1:8000/docs
```

Frontend can point to this backend with:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Current scope

Working today:

- PostgreSQL trip + itinerary + job storage (`db.py`, `orm_models.py`, `repository.py`)
- REST API aligned with `docs/web-backend-data-contract.md` (`main.py`, `models.py`)
- Background job lifecycle for generation (`agent.py`)

Available for the agent rewrite, not currently called:

- `llm.py` — DeepSeek JSON client with Langfuse tracing
- `amap.py` — AMap POI search / routing / weather, with fuzzy match filtering
- `observability.py` — Langfuse span + generation helpers

## 测试

```bash
# 冒烟测试验的是 API 契约与数据流，不需要真实 AI。
# 让服务带开关启动，可把单次测试从 2 分钟压到数秒，也不消耗 API 额度。
SKIP_AI_GENERATION=1 .venv/bin/uvicorn app.main:app --port 8000
python3 tests/smoke_test.py
```

AI 生成质量由 `scripts/` 下的专用脚本负责，与冒烟测试分开：

```bash
python3 scripts/llm_websearch_test.py deepseek-v4-flash dali
python3 scripts/llm_reliability_test.py deepseek-v4-flash
```

## Generation Agent

已接入，入口在 `app/generation.py`，由 `app/agent.py` 的 `run_generation_job` 调用。

```txt
POST /api/trips/{trip_id}/generate   -> { tripId, jobId }
GET  /api/jobs/{job_id}              -> { status, progress, message }
```

分工（依据见 `docs/Agent立项规划-v0.1.md` 的实测记录）：

| 层 | 负责 |
|---|---|
| LLM（deepseek-v4-flash） | 理解偏好、选点取舍、时段判断、写主题与理由 |
| Tavily 联网搜索 | 预约方式、门票优惠、无障碍设施、日落时间等时效信息 |
| 高德 | 地点是否存在、坐标、地址、真实通勤、天气 |
| 代码 | 地名三层匹配、通勤校正、住宿锚定、结构映射 |

生成耗时约 60~135 秒，随天数超线性增长。失败时退回占位骨架而非报错，
并在日志中记录完整堆栈。

Editing Agent（`POST /api/trips/{trip_id}/edit`）仍未实现。
