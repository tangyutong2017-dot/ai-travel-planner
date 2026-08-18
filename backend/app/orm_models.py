from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class TripRecord(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    dest: Mapped[str] = mapped_column(String(255))
    days: Mapped[int] = mapped_column(Integer)
    date: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), index=True)
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    attraction_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    itinerary: Mapped["ItineraryRecord | None"] = relationship(back_populates="trip", cascade="all, delete-orphan")
    jobs: Mapped[list["AgentJobRecord"]] = relationship(back_populates="trip", cascade="all, delete-orphan")


class ItineraryRecord(Base):
    __tablename__ = "itineraries"

    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True)
    origin_city: Mapped[str] = mapped_column(String(255), default="")
    destination: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    date_range: Mapped[str] = mapped_column(String(120))
    travelers_json: Mapped[dict] = mapped_column(JSONB)
    route_json: Mapped[list] = mapped_column(JSONB, default=list)
    interests_json: Mapped[list] = mapped_column(JSONB)
    notes_json: Mapped[list] = mapped_column(JSONB, default=list)
    days_json: Mapped[list] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    trip: Mapped[TripRecord] = relationship(back_populates="itinerary")


class ItineraryRevisionRecord(Base):
    """一次编辑前的行程快照，用于撤销。

    只存 days_json——所有编辑操作（改/删/加/移条目）都只动这一列，
    标题、同行人、备注不在编辑范围内。

    走快照而非逆操作：days_json 是单个 JSONB 列，整份行程就是一个 blob，
    复制一列即可。逆操作要为每个操作各写一个并保证正确（delete 还得记住
    被删条目的原始位置），出错面大得多。
    """

    __tablename__ = "itinerary_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    days_json: Mapped[list] = mapped_column(JSONB)
    label: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AgentJobRecord(Base):
    __tablename__ = "agent_jobs"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    trip_id: Mapped[str] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    progress: Mapped[int] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    trip: Mapped[TripRecord] = relationship(back_populates="jobs")
