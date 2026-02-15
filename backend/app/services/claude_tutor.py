import asyncio
import logging
from typing import List, Dict, Optional

from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError

from app.config import settings

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


tutor = ClaudeTutor()
