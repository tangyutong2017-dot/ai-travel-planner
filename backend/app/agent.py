import logging
import os

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


logger = logging.getLogger(__name__)


def skip_ai_generation() -> bool:
    """每次调用时读取，而不是 import 时——便于在同一进程里切换。"""
    return os.getenv("SKIP_AI_GENERATION", "").lower() in {"1", "true", "yes"}


def run_generation_job(job_id: str) -> None:
    """跑一次行程生成。

    维持 job 生命周期（create -> running -> succeeded/failed）与
    ``GET /api/jobs/{job_id}`` 轮询契约，前端向导与工作区无需改动。

    生成失败时退回占位行程而不是让任务失败——用户已经等了一分多钟，
    给一份可编辑的骨架比一句报错有用。

    设 ``SKIP_AI_GENERATION=1`` 可跳过 AI 直接产出占位行程。冒烟测试用它——
    那些断言验的是 API 契约与数据流，AI 质量归 scripts/ 下的专用脚本管。
    否则单次测试要等一次真实生成（60~135 秒）并消耗 API 额度。
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
            if skip_ai_generation():
                report(50, "已跳过 AI 生成（SKIP_AI_GENERATION）")
                itinerary = create_placeholder_itinerary(job.tripId, payload)
            else:
                itinerary = generate_itinerary(job.tripId, payload, report)
        except Exception as exc:
            # 兜底会掩盖真实故障：生成失败时界面看起来只是「质量差」，
            # 而非「agent 根本没跑」。日志留全栈，job message 只给摘要。
            logger.exception("行程生成失败，退回占位骨架：%s", exc)
            fallback_reason = str(exc)
            itinerary = create_placeholder_itinerary(job.tripId, payload)

        update_agent_job(db, job_id, "running", 98, "正在保存行程并同步工作区")
        save_itinerary(db, job.tripId, itinerary)

        update_agent_job(
            db,
            job_id,
            "succeeded",
            100,
            # 给用户的消息不带内部符号名——实测泄露过 "name 'resolve_stays' is not defined"。
            # 完整堆栈已写进日志，排查看日志即可。
            "AI 生成未完成，已给出可编辑的行程骨架，你可以手动调整或重新生成"
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
