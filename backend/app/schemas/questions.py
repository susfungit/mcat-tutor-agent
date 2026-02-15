"""Request/response schemas for practice mode."""

from typing import Optional, List, Dict

from pydantic import BaseModel, Field


class QuestionGenerateRequest(BaseModel):
    section: str = Field(max_length=200)
    topic: str = Field(max_length=100)
    subtopic: Optional[str] = Field(default=None, max_length=200)
    difficulty: int = Field(ge=1, le=10, default=5)
    question_type: str = Field(default="discrete", pattern="^(discrete|passage)$")


class QuestionOut(BaseModel):
    """Question response — excludes correct_answer to prevent cheating."""

    id: int
    section: str
    topic: str
    subtopic: Optional[str] = None
    difficulty: int
    question_type: str
    stem: str
    passage: Optional[str] = None
    options: Dict[str, str]
    concepts_tested: Optional[List[str]] = None
    high_yield: bool

    model_config = {"from_attributes": True}


class AnswerRequest(BaseModel):
    question_id: int
    selected_answer: str = Field(pattern="^[A-D]$")
    session_id: Optional[int] = None
    time_spent_seconds: Optional[int] = Field(default=None, ge=0)


class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: dict
    xp_earned: int
    mastery_level: float
