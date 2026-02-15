"""Integration tests for question generation and answer endpoints."""

import json

import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import mock_claude_response

SAMPLE_QUESTION_JSON = json.dumps({
    "stem": "What is the pH of a 0.01 M HCl solution?",
    "options": {
        "A": "1",
        "B": "2",
        "C": "3",
        "D": "4",
    },
    "correct_answer": "B",
    "explanation": {
        "why_correct": "HCl is a strong acid, pH = -log(0.01) = 2",
        "why_wrong": {
            "A": "This would be 0.1 M HCl",
            "C": "This would be 0.001 M HCl",
            "D": "This would be 0.0001 M HCl",
        },
    },
    "concepts_tested": ["acid-base chemistry", "pH calculation"],
    "high_yield": True,
})


@pytest.mark.asyncio
async def test_generate_question(client, auth_headers):
    with mock_claude_response(SAMPLE_QUESTION_JSON):
        resp = await client.post(
            "/api/questions/generate",
            headers=auth_headers,
            json={
                "section": "Chemical and Physical Foundations of Biological Systems",
                "topic": "General Chemistry",
                "difficulty": 3,
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["stem"] == "What is the pH of a 0.01 M HCl solution?"
    assert "A" in data["options"]
    assert "correct_answer" not in data  # Must not be exposed
    assert data["question_type"] == "discrete"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_generate_passage_question(client, auth_headers):
    passage_json = json.dumps({
        "passage": "A researcher measured the pH of various solutions...",
        "stem": "Based on the passage, which solution is most acidic?",
        "options": {"A": "Sol A", "B": "Sol B", "C": "Sol C", "D": "Sol D"},
        "correct_answer": "A",
        "explanation": {
            "why_correct": "Solution A has the lowest pH",
            "why_wrong": {"B": "Higher pH", "C": "Higher pH", "D": "Higher pH"},
        },
        "concepts_tested": ["pH"],
        "high_yield": False,
    })
    with mock_claude_response(passage_json):
        resp = await client.post(
            "/api/questions/generate",
            headers=auth_headers,
            json={
                "section": "Chemical and Physical Foundations of Biological Systems",
                "topic": "General Chemistry",
                "difficulty": 5,
                "question_type": "passage",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["passage"] is not None
    assert data["question_type"] == "passage"


@pytest.mark.asyncio
async def test_answer_correct(client, auth_headers):
    with mock_claude_response(SAMPLE_QUESTION_JSON):
        gen_resp = await client.post(
            "/api/questions/generate",
            headers=auth_headers,
            json={
                "section": "Chemical and Physical Foundations of Biological Systems",
                "topic": "General Chemistry",
                "difficulty": 3,
            },
        )
    question_id = gen_resp.json()["id"]

    resp = await client.post(
        "/api/questions/answer",
        headers=auth_headers,
        json={"question_id": question_id, "selected_answer": "B"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is True
    assert data["correct_answer"] == "B"
    assert data["xp_earned"] > 0
    assert data["mastery_level"] == 0.05
    assert "why_correct" in data["explanation"]


@pytest.mark.asyncio
async def test_answer_incorrect(client, auth_headers):
    with mock_claude_response(SAMPLE_QUESTION_JSON):
        gen_resp = await client.post(
            "/api/questions/generate",
            headers=auth_headers,
            json={
                "section": "Chemical and Physical Foundations of Biological Systems",
                "topic": "General Chemistry",
                "difficulty": 5,
            },
        )
    question_id = gen_resp.json()["id"]

    resp = await client.post(
        "/api/questions/answer",
        headers=auth_headers,
        json={"question_id": question_id, "selected_answer": "A"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_correct"] is False
    assert data["xp_earned"] == 0
    assert data["mastery_level"] == 0.0  # clamped at 0.0 (can't go negative)


@pytest.mark.asyncio
async def test_answer_incorrect_mastery_clamped_at_zero(client, auth_headers):
    """Mastery should not go below 0.0."""
    with mock_claude_response(SAMPLE_QUESTION_JSON):
        gen_resp = await client.post(
            "/api/questions/generate",
            headers=auth_headers,
            json={
                "section": "Chemical and Physical Foundations of Biological Systems",
                "topic": "General Chemistry",
                "difficulty": 5,
            },
        )
    question_id = gen_resp.json()["id"]

    resp = await client.post(
        "/api/questions/answer",
        headers=auth_headers,
        json={"question_id": question_id, "selected_answer": "A"},
    )
    # Mastery starts at 0.0, goes down by 0.02 but clamped to 0.0
    assert resp.json()["mastery_level"] >= 0.0


@pytest.mark.asyncio
async def test_duplicate_answer_rejected(client, auth_headers):
    with mock_claude_response(SAMPLE_QUESTION_JSON):
        gen_resp = await client.post(
            "/api/questions/generate",
            headers=auth_headers,
            json={
                "section": "Chemical and Physical Foundations of Biological Systems",
                "topic": "General Chemistry",
                "difficulty": 3,
            },
        )
    question_id = gen_resp.json()["id"]

    # First answer
    await client.post(
        "/api/questions/answer",
        headers=auth_headers,
        json={"question_id": question_id, "selected_answer": "B"},
    )

    # Duplicate
    resp = await client.post(
        "/api/questions/answer",
        headers=auth_headers,
        json={"question_id": question_id, "selected_answer": "A"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_answer_nonexistent_question(client, auth_headers):
    resp = await client.post(
        "/api/questions/answer",
        headers=auth_headers,
        json={"question_id": 99999, "selected_answer": "A"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_answer_invalid_choice(client, auth_headers):
    """selected_answer must be A-D."""
    resp = await client.post(
        "/api/questions/answer",
        headers=auth_headers,
        json={"question_id": 1, "selected_answer": "E"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_generate_requires_auth(client):
    resp = await client.post(
        "/api/questions/generate",
        json={
            "section": "Chemical and Physical Foundations of Biological Systems",
            "topic": "General Chemistry",
            "difficulty": 5,
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_cached_question_reused(client, auth_headers):
    """Second generate call should return cached question without calling Claude."""
    with mock_claude_response(SAMPLE_QUESTION_JSON):
        resp1 = await client.post(
            "/api/questions/generate",
            headers=auth_headers,
            json={
                "section": "Chemical and Physical Foundations of Biological Systems",
                "topic": "General Chemistry",
                "difficulty": 3,
            },
        )

    # Don't mock Claude — if it tries to call, it would fail.
    # The cached question should be returned since user hasn't answered it.
    resp2 = await client.post(
        "/api/questions/generate",
        headers=auth_headers,
        json={
            "section": "Chemical and Physical Foundations of Biological Systems",
            "topic": "General Chemistry",
            "difficulty": 3,
        },
    )
    assert resp2.status_code == 200
    assert resp2.json()["id"] == resp1.json()["id"]
