"""Per-user per-topic mastery tracking."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class TutorMemory(Base):
    __tablename__ = "tutor_memory"
    __table_args__ = (
        UniqueConstraint("user_id", "topic", "subtopic", name="uq_user_topic_subtopic"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    section: Mapped[str] = mapped_column(String, nullable=False)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    subtopic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mastery_level: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mistake_patterns: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
