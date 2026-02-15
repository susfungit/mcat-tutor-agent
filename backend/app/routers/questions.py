"""Practice mode endpoints: generate questions and submit answers."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.question import Question
from app.models.tutor_memory import TutorMemory
from app.models.user import User
from app.models.user_response import UserResponse
from app.schemas.questions import (
    QuestionGenerateRequest,
    QuestionOut,
    AnswerRequest,
    AnswerResponse,
)
from app.services.claude_tutor import TutorServiceError
from app.services.question_generator import question_generator
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/questions", tags=["questions"])
limiter = Limiter(key_func=get_remote_address)

# XP rewards by difficulty tier
XP_BY_DIFFICULTY = {
    range(1, 4): 10,   # Easy: 10 XP
    range(4, 7): 20,   # Medium: 20 XP
    range(7, 11): 35,  # Hard: 35 XP
}


def _calculate_xp(difficulty: int) -> int:
    for diff_range, xp in XP_BY_DIFFICULTY.items():
        if difficulty in diff_range:
            return xp
    return 10


@router.post("/generate", response_model=QuestionOut)
@limiter.limit("20/minute")
async def generate_question(
    request: Request,
    body: QuestionGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        question = await question_generator.get_or_generate_question(
            user_id=current_user.id,
            section=body.section,
            topic=body.topic,
            subtopic=body.subtopic,
            difficulty=body.difficulty,
            question_type=body.question_type,
            db=db,
        )
    except TutorServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return QuestionOut.model_validate(question)


@router.post("/answer", response_model=AnswerResponse)
@limiter.limit("60/minute")
async def answer_question(
    request: Request,
    body: AnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Load the question
    result = await db.execute(
        select(Question).where(Question.id == body.question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Prevent duplicate answers
    result = await db.execute(
        select(UserResponse).where(
            and_(
                UserResponse.user_id == current_user.id,
                UserResponse.question_id == body.question_id,
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="You have already answered this question"
        )

    # Check answer
    is_correct = body.selected_answer == question.correct_answer
    xp_earned = _calculate_xp(question.difficulty) if is_correct else 0

    # Save user response
    user_response = UserResponse(
        user_id=current_user.id,
        question_id=body.question_id,
        session_id=body.session_id,
        selected_answer=body.selected_answer,
        is_correct=is_correct,
        time_spent_seconds=body.time_spent_seconds,
        xp_earned=xp_earned,
    )
    db.add(user_response)

    # Update TutorMemory mastery_level
    result = await db.execute(
        select(TutorMemory).where(
            and_(
                TutorMemory.user_id == current_user.id,
                TutorMemory.topic == question.topic,
                TutorMemory.subtopic == question.subtopic,
            )
        )
    )
    memory = result.scalar_one_or_none()
    if not memory:
        memory = TutorMemory(
            user_id=current_user.id,
            section=question.section,
            topic=question.topic,
            subtopic=question.subtopic,
        )
        db.add(memory)
        await db.flush()

    memory.attempt_count += 1
    if is_correct:
        memory.correct_count += 1
        memory.mastery_level = min(1.0, memory.mastery_level + 0.05)
    else:
        memory.mastery_level = max(0.0, memory.mastery_level - 0.02)
    memory.last_reviewed_at = datetime.now(timezone.utc)

    return AnswerResponse(
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        xp_earned=xp_earned,
        mastery_level=memory.mastery_level,
    )
