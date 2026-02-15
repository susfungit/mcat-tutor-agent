"""Shared test fixtures: in-memory DB, test client, auth helpers."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.main import limiter as main_limiter
from app.routers.auth import limiter as auth_limiter
from app.routers.tutor import limiter as tutor_limiter
from app.routers.questions import limiter as questions_limiter

_all_limiters = [main_limiter, auth_limiter, tutor_limiter, questions_limiter]


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """Async test client with DB override and rate limiting disabled."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    # Disable all rate limiters for tests
    for lim in _all_limiters:
        lim.enabled = False

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    for lim in _all_limiters:
        lim.enabled = True
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_token(client):
    """Register a test user and return a valid access token."""
    await client.post(
        "/api/auth/register",
        json={"email": "test@test.com", "password": "testpass123", "name": "Test"},
    )
    resp = await client.post(
        "/api/auth/login",
        data={"username": "test@test.com", "password": "testpass123"},
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token):
    """Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


def mock_claude_response(text: str):
    """Patch ClaudeTutor.chat to return a fixed response without calling the API."""
    return patch(
        "app.services.claude_tutor.ClaudeTutor.chat",
        new_callable=AsyncMock,
        return_value=text,
    )
