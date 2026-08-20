import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Response
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .agent import get_generation_job, run_generation_job, start_generation_job
from .amap import static_map_png
from .editing import EditRejected, PlaceNotFoundError, apply_ops, build_verified_item, plan_edits
from .db import get_db, init_db, SessionLocal
from .models import (
    AgentJob,
    ChatEditPayload,
    ChatEditResult,
    CreateTripPayload,
    CreateTripResponse,
    GenerateTripResponse,
    InsertItineraryItemPayload,
    Itinerary,
    Trip,
    TripListResponse,
    TripStatus,
    UndoResult,
    UpdateItineraryItemPayload,
    UpdateTripPayload,
)
from .repository import (
    create_trip,
    delete_itinerary_item,
    delete_trip,
    get_itinerary,
    get_trip,
    insert_itinerary_item,
    list_trips,
    save_itinerary,
    seed_initial_data,
    undo_count,
    undo_last_edit,
    update_itinerary_item,
    update_trip_name,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """建表与种子数据。取代已废弃的 @app.on_event("startup")。"""
    init_db()
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()
    yield


logger = logging.getLogger(__name__)

app = FastAPI(title="Travel Planner API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    """根路径原本没有路由，直接访问会返回 404「Not Found」，看起来像服务挂了。

    这里给出一句指路：这是 API 服务，前端在另一个端口。
    """
    return {
        "service": "Travel Planner API",
        "docs": "/docs",
        "health": "/health",
        "web": "前端开发服务器在 http://localhost:5173",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/trips", response_model=TripListResponse)
def get_trips(
    status: TripStatus | None = Query(default=None),
    keyword: str | None = Query(default=None),
    sort: str = Query(default="updatedAt_desc"),
    db: Session = Depends(get_db),
) -> TripListResponse:
    return list_trips(db, status=status, keyword=keyword, sort=sort)


@app.post("/api/trips", response_model=CreateTripResponse)
def post_trip(payload: CreateTripPayload, db: Session = Depends(get_db)) -> CreateTripResponse:
    trip = create_trip(db, payload)
    return CreateTripResponse(tripId=trip.id)


@app.get("/api/trips/{trip_id}", response_model=Itinerary)
def get_trip_detail(trip_id: str, db: Session = Depends(get_db)) -> Itinerary:
    itinerary = get_itinerary(db, trip_id)
    if itinerary:
        return itinerary

    if not get_trip(db, trip_id):
        raise HTTPException(status_code=404, detail="行程不存在或已被删除")

    raise HTTPException(status_code=409, detail="该行程还没有生成过内容")


@app.delete("/api/trips/{trip_id}")
def delete_trip_route(trip_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    if not delete_trip(db, trip_id):
        raise HTTPException(status_code=404, detail="行程不存在或已被删除")

    return {"tripId": trip_id}


@app.patch("/api/trips/{trip_id}", response_model=Trip)
def update_trip_route(
    trip_id: str,
    payload: UpdateTripPayload,
    db: Session = Depends(get_db),
) -> Trip:
    updated = update_trip_name(db, trip_id, payload.name)
    if not updated:
        raise HTTPException(status_code=404, detail="行程不存在或已被删除")

    return updated


@app.delete("/api/trips/{trip_id}/days/{day_number}/items/{item_id}", response_model=Itinerary)
def delete_trip_item_route(
    trip_id: str,
    day_number: int,
    item_id: str,
    db: Session = Depends(get_db),
) -> Itinerary:
    updated = delete_itinerary_item(db, trip_id, day_number, item_id)
    if not updated:
        raise HTTPException(status_code=404, detail="没有找到这个行程项目")

    return updated


@app.post("/api/trips/{trip_id}/days/{day_number}/items", response_model=Itinerary)
def insert_trip_item_route(
    trip_id: str,
    day_number: int,
    payload: InsertItineraryItemPayload,
    db: Session = Depends(get_db),
) -> Itinerary:
    itinerary = get_itinerary(db, trip_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="没有找到这个行程")

    try:
        item = build_verified_item(trip_id, day_number, itinerary.destination, payload)
    except PlaceNotFoundError as exc:
        # 如实说查不到，而不是放一个没有坐标的条目进去充数
        raise HTTPException(status_code=422, detail=f"高德地图查不到「{exc.name}」，没有添加") from exc

    updated = insert_itinerary_item(db, trip_id, day_number, item, payload.afterItemId)
    if not updated:
        raise HTTPException(status_code=404, detail="没有找到这一天")

    return updated


@app.patch("/api/trips/{trip_id}/days/{day_number}/items/{item_id}", response_model=Itinerary)
def update_trip_item_route(
    trip_id: str,
    day_number: int,
    item_id: str,
    payload: UpdateItineraryItemPayload,
    db: Session = Depends(get_db),
) -> Itinerary:
    updated = update_itinerary_item(db, trip_id, day_number, item_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="没有找到这个行程项目")

    return updated


@app.post("/api/trips/{trip_id}/chat", response_model=ChatEditResult)
def chat_edit_route(
    trip_id: str,
    payload: ChatEditPayload,
    db: Session = Depends(get_db),
) -> ChatEditResult:
    """用一句话修改行程。

    走同步请求而非 job 轮询：实测单次 2.7~5.6 秒，而生成要 60~135 秒——
    后者需要异步是因为要吐整份行程，这里只吐一两个操作。
    """
    itinerary = get_itinerary(db, trip_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="行程不存在或还没有生成过内容")

    try:
        ops, reply = plan_edits(itinerary, payload.message)
    except EditRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        # 模型超时或不可用。行程没动，如实说一句就好——内部细节只进日志
        logger.exception("对话编辑调用模型失败 trip=%s", trip_id)
        raise HTTPException(status_code=503, detail="AI 服务暂时不可用，行程未改动") from exc

    # 模型只回文字不调工具是正常路径：它在澄清，或在说这件事做不到
    if not ops:
        return ChatEditResult(reply=reply or "我不太确定要改什么，换个说法再说一次？",
                              undoRemaining=undo_count(db, trip_id))

    try:
        updated, changes, touched = apply_ops(itinerary, ops)
    except EditRejected as exc:
        # 全成功或全不动：一条校验不过就整条作废，不留中间状态
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not changes:
        # 模型给了操作，但每个字段都与原值相同（常见于「改成 1 小时」而原本就是
        # 60 分钟）。不写库、不留快照，也不谎称改过
        return ChatEditResult(
            reply=reply or "看下来这处本来就是这样，没有改动。",
            undoRemaining=undo_count(db, trip_id),
        )

    # 一条指令一份快照——用户撤销时期望撤销的是「刚才那句话」，不是点三次
    save_itinerary(db, trip_id, updated, snapshot_label=payload.message[:120])

    return ChatEditResult(
        reply=reply,
        changes=changes,
        changedItemIds=touched,
        itinerary=updated,
        undoRemaining=undo_count(db, trip_id),
    )


@app.get("/api/trips/{trip_id}/undo", response_model=UndoResult)
def get_undo_state_route(trip_id: str, db: Session = Depends(get_db)) -> UndoResult:
    return UndoResult(remaining=undo_count(db, trip_id))


@app.post("/api/trips/{trip_id}/undo", response_model=UndoResult)
def undo_trip_edit_route(trip_id: str, db: Session = Depends(get_db)) -> UndoResult:
    restored = undo_last_edit(db, trip_id)
    if not restored:
        # 没有可撤销的改动与行程不存在是两回事，但对调用方是同一种处置：
        # 按钮置灰。合成一个 409 比让前端区分两种 404 更省事。
        raise HTTPException(status_code=409, detail="没有可撤销的改动")

    return UndoResult(remaining=undo_count(db, trip_id), itinerary=restored)


@app.get("/api/trips/{trip_id}/days/{day_number}/map.png")
def get_day_map(
    trip_id: str,
    day_number: int,
    width: int = Query(default=480, ge=120, le=1024),
    height: int = Query(default=320, ge=120, le=1024),
    db: Session = Depends(get_db),
) -> Response:
    """当日动线的静态地图。

    走后端代理而非前端直连，是为了让高德 key 留在服务端。
    没有任何坐标时返回 404——由前端决定怎么兜底，不画一张空地图冒充。
    """
    itinerary = get_itinerary(db, trip_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="行程不存在或还没有生成过内容")

    day = next((d for d in itinerary.days if d.day == day_number), None)
    if not day:
        raise HTTPException(status_code=404, detail="没有这一天的行程")

    points = [
        (item.location["lat"], item.location["lng"])
        for item in day.items
        if item.location and "lat" in item.location and "lng" in item.location
    ]
    if not points:
        raise HTTPException(status_code=404, detail="这一天还没有已核实的坐标")

    try:
        png = static_map_png(points, width=width, height=height)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"地图服务暂时不可用：{exc}") from exc

    if not png:
        raise HTTPException(status_code=404, detail="这一天还没有已核实的坐标")

    # 坐标不变则图不变，缓存一天，省掉重复的高德调用
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


@app.post("/api/trips/{trip_id}/generate", response_model=GenerateTripResponse)
def generate_trip(
    trip_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> GenerateTripResponse:
    if not get_trip(db, trip_id):
        raise HTTPException(status_code=404, detail="行程不存在或已被删除")

    job = start_generation_job(trip_id)
    background_tasks.add_task(run_generation_job, job.jobId)
    return GenerateTripResponse(tripId=trip_id, jobId=job.jobId)


@app.get("/api/jobs/{job_id}", response_model=AgentJob)
def get_job(job_id: str) -> AgentJob:
    job = get_generation_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="生成任务不存在或已过期")

    return job
