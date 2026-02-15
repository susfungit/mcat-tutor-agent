"""Generate MCAT questions via Claude, cache in DB, retry on parse failures."""

import logging
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question
from app.models.user_response import UserResponse
from app.prompts.question_gen import DISCRETE_QUESTION_PROMPT, PASSAGE_QUESTION_PROMPT
from app.services.claude_tutor import tutor, TutorServiceError
from app.utils.json_parser import parse_llm_json, JSONParseError

logger = logging.getLogger(__name__)

MAX_RETRIES = 2

GENERATE_SYSTEM_PROMPT = (
    "You are an MCAT question generator. Return ONLY valid JSON, no markdown "
    "formatting, no explanation text. Follow the exact schema requested."
)


class QuestionGenerator:
    async def get_or_generate_question(
        self,
        user_id: int,
        section: str,
        topic: str,
        subtopic: Optional[str],
        difficulty: int,
        question_type: str,
        db: AsyncSession,
    ) -> Question:
        """Find a cached unanswered question or generate a new one."""
        # Find a question the user hasn't answered yet
        answered_subq = (
            select(UserResponse.question_id)
            .where(UserResponse.user_id == user_id)
            .subquery()
        )

        filters = [
            Question.section == section,
            Question.topic == topic,
            Question.question_type == question_type,
            Question.id.notin_(select(answered_subq.c.question_id)),
        ]
        if subtopic:
            filters.append(Question.subtopic == subtopic)
        # Allow +/- 2 difficulty range for cache hits
        filters.append(Question.difficulty >= max(1, difficulty - 2))
        filters.append(Question.difficulty <= min(10, difficulty + 2))

        result = await db.execute(
            select(Question).where(and_(*filters)).limit(1)
        )
        cached = result.scalar_one_or_none()
        if cached:
            return cached

        # Generate a new question
        return await self._generate_question(
            section, topic, subtopic, difficulty, question_type, db
        )

    async def _generate_question(
        self,
        section: str,
        topic: str,
        subtopic: Optional[str],
        difficulty: int,
        question_type: str,
        db: AsyncSession,
    ) -> Question:
        """Call Claude to generate a question, parse JSON, persist to DB."""
        template = (
            PASSAGE_QUESTION_PROMPT if question_type == "passage"
            else DISCRETE_QUESTION_PROMPT
        )
        if difficulty <= 3:
            difficulty_description = "basic recall"
        elif difficulty <= 6:
            difficulty_description = "application and analysis"
        else:
            difficulty_description = "complex multi-step reasoning"

        prompt_text = template.format(
            section=section,
            topic=topic,
            subtopic=subtopic or topic,
            difficulty=difficulty,
            difficulty_description=difficulty_description,
        )

        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                raw_response = await tutor.chat(
                    user_message=prompt_text,
                    conversation_history=[],
                    system_prompt=GENERATE_SYSTEM_PROMPT,
                )
                data = parse_llm_json(raw_response)

                question = Question(
                    section=section,
                    topic=topic,
                    subtopic=subtopic,
                    difficulty=difficulty,
                    question_type=question_type,
                    stem=data["stem"],
                    passage=data.get("passage"),
                    options=data["options"],
                    correct_answer=data["correct_answer"],
                    explanation=data["explanation"],
                    concepts_tested=data.get("concepts_tested"),
                    high_yield=data.get("high_yield", False),
                )
                db.add(question)
                await db.flush()
                return question

            except JSONParseError as e:
                last_error = e
                logger.warning(
                    "JSON parse failed on attempt %d: %s", attempt + 1, e
                )
            except TutorServiceError:
                raise
            except (KeyError, TypeError) as e:
                last_error = e
                logger.warning(
                    "Invalid question data on attempt %d: %s", attempt + 1, e
                )

        raise TutorServiceError(
            f"Failed to generate question after {MAX_RETRIES + 1} attempts: {last_error}"
        )


question_generator = QuestionGenerator()
