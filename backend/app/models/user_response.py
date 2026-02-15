"""Student answer records for practice questions."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class UserResponse(Base):
    __tablename__ = "user_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("questions.id"), nullable=False, index=True
    )
    session_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("study_sessions.id"), nullable=True
    )
    selected_answer: Mapped[str] = mapped_column(String(1), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_spent_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
