"""生成任务（agent job）的生命周期记录。"""

from uuid import uuid4

from sqlalchemy.orm import Session

from ..models import AgentJob
from ..orm_models import AgentJobRecord
from .mappers import job_from_record


def create_agent_job(db: Session, trip_id: str) -> AgentJob:
    job_id = f"job_{uuid4().hex[:12]}"
    record = AgentJobRecord(
        id=job_id,
        trip_id=trip_id,
        status="queued",
        progress=8,
        message="任务已进入队列",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return job_from_record(record)


def get_agent_job(db: Session, job_id: str) -> AgentJob | None:
    record = db.get(AgentJobRecord, job_id)
    return job_from_record(record) if record else None


def update_agent_job(db: Session, job_id: str, status: str, progress: int, message: str) -> AgentJob | None:
    record = db.get(AgentJobRecord, job_id)
    if not record:
        return None

    record.status = status
    record.progress = progress
    record.message = message
    db.commit()
    db.refresh(record)
    return job_from_record(record)
