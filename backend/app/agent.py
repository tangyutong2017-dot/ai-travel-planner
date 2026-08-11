from .db import SessionLocal
from .generation_fast import generate_fast_itinerary
from .models import AgentJob
from .repository import (
    create_agent_job,
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
    """Run the fast MVP generation workflow for one trip."""
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
        itinerary, metadata = generate_fast_itinerary(job.tripId, payload)

        update_agent_job(db, job_id, "running", 88, "正在保存行程并同步工作区")
        save_itinerary(db, job.tripId, itinerary)

        evaluation = metadata.get("evaluation") or {}
        score = evaluation.get("score")
        suffix = f"；质量评分 {score}" if score is not None else ""
        update_agent_job(
            db,
            job_id,
            "succeeded",
            100,
            f"行程已生成，可进入工作区继续编辑{suffix}",
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
