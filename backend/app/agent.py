from .db import SessionLocal
from .generation import generate_itinerary
from .models import AgentJob
from .repository import (
    create_agent_job,
    create_placeholder_itinerary,
    get_agent_job,
    get_trip,
    get_trip_payload,
    save_itinerary,
    update_agent_job,
)


def start_generation_job(trip_id: str) -> AgentJob:
    """Create a generation job record and return it to the frontend."""
    db = SessionLocal()
    try:
        return create_agent_job(db, trip_id)
    finally:
        db.close()


def run_generation_job(job_id: str) -> None:
    """跑一次行程生成。

    维持 job 生命周期（create -> running -> succeeded/failed）与
    ``GET /api/jobs/{job_id}`` 轮询契约，前端向导与工作区无需改动。

    生成失败时退回占位行程而不是让任务失败——用户已经等了一分多钟，
    给一份可编辑的骨架比一句报错有用。
    """
    db = SessionLocal()
    try:
        job = get_agent_job(db, job_id)
        if not job:
            return

        update_agent_job(db, job_id, "running", 20, "正在读取行程需求")

        payload = get_trip_payload(db, job.tripId)
        if not payload:
            update_agent_job(db, job_id, "failed", 100, "找不到创建行程时的请求数据")
            return

        if not get_trip(db, job.tripId):
            update_agent_job(db, job_id, "failed", 100, "行程不存在或已被删除")
            return

        def report(progress: int, message: str) -> None:
            update_agent_job(db, job_id, "running", progress, message)

        fallback_reason = ""
        try:
            itinerary = generate_itinerary(job.tripId, payload, report)
        except Exception as exc:
            fallback_reason = str(exc)
            itinerary = create_placeholder_itinerary(job.tripId, payload)

        update_agent_job(db, job_id, "running", 98, "正在保存行程并同步工作区")
        save_itinerary(db, job.tripId, itinerary)

        update_agent_job(
            db,
            job_id,
            "succeeded",
            100,
            f"AI 生成未完成（{fallback_reason[:60]}），已给出可编辑的行程骨架"
            if fallback_reason
            else "行程已生成，可进入工作区继续编辑",
        )
    except Exception as exc:
        db.rollback()
        update_agent_job(db, job_id, "failed", 100, f"生成任务失败：{exc}")
    finally:
        db.close()


def get_generation_job(job_id: str) -> AgentJob | None:
    db = SessionLocal()
    try:
        return get_agent_job(db, job_id)
    finally:
        db.close()
