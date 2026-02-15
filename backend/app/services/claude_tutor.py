import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.tutor_memory import TutorMemory
from app.models.conversation import ConversationMessage
from app.prompts.socratic import build_socratic_prompt

logger = logging.getLogger(__name__)


class TutorServiceError(Exception):
    """Raised when the Claude API call fails."""

    pass


DEFAULT_SYSTEM_PROMPT = (
    "You are an expert MCAT tutor. You help students prepare for the MCAT exam. "
    "Be encouraging but rigorous. When a student asks a question, guide them toward "
    "understanding rather than just giving the answer. Keep responses concise and focused."
)


class ClaudeTutor:
    def __init__(self):
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    async def chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        messages = conversation_history + [
            {"role": "user", "content": user_message}
        ]

        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=1024,
                system=system_prompt or DEFAULT_SYSTEM_PROMPT,
                messages=messages,
            )
            return response.content[0].text
        except RateLimitError:
            logger.warning("Claude API rate limit hit")
            raise TutorServiceError(
                "The tutor is currently busy. Please try again in a moment."
            )
        except APIConnectionError:
            logger.error("Failed to connect to Claude API")
            raise TutorServiceError(
                "Unable to reach the tutor service. Please try again later."
            )
        except APIError as e:
            logger.error("Claude API error: %s", e)
            raise TutorServiceError(
                "The tutor encountered an error. Please try again."
            )

    async def socratic_chat(
        self,
        user_id: int,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        section: str,
        topic: str,
        concept: str,
        session_id: int,
        db: AsyncSession,
    ) -> Tuple[str, int]:
        """Socratic tutoring with adaptive escalation.

        Returns (response_text, escalation_level).
        """
        # Load or create TutorMemory for this user+topic+concept
        result = await db.execute(
            select(TutorMemory).where(
                and_(
                    TutorMemory.user_id == user_id,
                    TutorMemory.topic == topic,
                    TutorMemory.subtopic == concept,
                )
            )
        )
        memory = result.scalar_one_or_none()
        if not memory:
            memory = TutorMemory(
                user_id=user_id,
                section=section,
                topic=topic,
                subtopic=concept,
            )
            db.add(memory)
            await db.flush()

        # Count concept attempts in this session to determine escalation
        result = await db.execute(
            select(ConversationMessage).where(
                and_(
                    ConversationMessage.session_id == session_id,
                    ConversationMessage.role == "user",
                    ConversationMessage.concept == concept,
                )
            )
        )
        session_attempts = len(result.scalars().all())
        # +1 for current message; map to escalation 1-5
        escalation_level = min(5, (session_attempts // 2) + 1)

        # Build adaptive system prompt
        system_prompt = build_socratic_prompt(section, topic, concept, escalation_level)

        # Call Claude via existing chat() method (reuses error handling + asyncio.to_thread)
        response_text = await self.chat(user_message, conversation_history, system_prompt)

        # Update memory
        memory.attempt_count += 1
        memory.last_reviewed_at = datetime.now(timezone.utc)

        return response_text, escalation_level


tutor = ClaudeTutor()
