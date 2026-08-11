from .db import SessionLocal
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
    """Fill one trip with a placeholder itinerary.

    The Generation Agent is being redesigned. This function keeps the
    job lifecycle (create -> running -> succeeded/failed) and the
    ``GET /api/jobs/{job_id}`` polling contract intact, so the wizard and
    the workspace still work end to end. Swap the placeholder call below
    for the new agent when it lands.
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

        update_agent_job(db, job_id, "running", 35, "正在生成初版行程")
        itinerary = create_placeholder_itinerary(job.tripId, payload)

        update_agent_job(db, job_id, "running", 88, "正在保存行程并同步工作区")
        save_itinerary(db, job.tripId, itinerary)

        update_agent_job(
            db,
            job_id,
            "succeeded",
            100,
            "已生成占位行程；Generation Agent 重写中",
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
