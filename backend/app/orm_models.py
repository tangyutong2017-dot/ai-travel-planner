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
    destination: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    date_range: Mapped[str] = mapped_column(String(120))
    travelers: Mapped[int] = mapped_column(Integer)
    interests_json: Mapped[list] = mapped_column(JSONB)
    days_json: Mapped[list] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    trip: Mapped[TripRecord] = relationship(back_populates="itinerary")


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
