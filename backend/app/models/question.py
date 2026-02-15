"""Generated MCAT questions stored for caching and reuse."""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import Integer, String, Text, Float, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    section: Mapped[str] = mapped_column(String, nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subtopic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String, nullable=False, default="discrete"
    )  # "discrete" or "passage"
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    passage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    options: Mapped[dict] = mapped_column(JSON, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(1), nullable=False)
    explanation: Mapped[dict] = mapped_column(JSON, nullable=False)
    concepts_tested: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    high_yield: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
