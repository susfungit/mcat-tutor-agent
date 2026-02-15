import logging
import secrets
from pathlib import Path

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Resolve .env relative to this file's directory (backend/app/../.env = backend/.env)
_env_file = Path(__file__).resolve().parent.parent / ".env"

_INSECURE_DEFAULTS = {"change-me", "change-me-to-a-random-string", "secret", ""}


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./mcat_tutor.db"
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ANTHROPIC_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = {"env_file": str(_env_file), "env_file_encoding": "utf-8"}


settings = Settings()

if settings.SECRET_KEY in _INSECURE_DEFAULTS:
    logger.warning(
        "SECRET_KEY is set to an insecure default! "
        "JWTs will not persist across restarts. "
        "Set a strong SECRET_KEY in your .env file for production."
    )
