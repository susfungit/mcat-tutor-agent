"""Integration tests for the Socratic chat endpoint."""

import json

import pytest

from tests.conftest import mock_claude_response


@pytest.mark.asyncio
async def test_socratic_chat_creates_session(client, auth_headers):
    with mock_claude_response("What do you already know about enzymes?"):
        resp = await client.post(
            "/api/tutor/socratic",
            headers=auth_headers,
            json={
                "content": "Help me with enzyme kinetics",
                "section": "Biological and Biochemical Foundations of Living Systems",
                "topic": "Biochemistry",
                "concept": "Enzyme Kinetics",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] is not None
    assert data["escalation_level"] == 1
    assert data["topic"] == "Biochemistry"
    assert data["concept"] == "Enzyme Kinetics"
    assert "enzymes" in data["response"].lower()


@pytest.mark.asyncio
async def test_socratic_chat_reuses_session(client, auth_headers):
    with mock_claude_response("Tell me more."):
        resp1 = await client.post(
            "/api/tutor/socratic",
            headers=auth_headers,
            json={
                "content": "What is Km?",
                "section": "Biological and Biochemical Foundations of Living Systems",
                "topic": "Biochemistry",
                "concept": "Enzyme Kinetics",
            },
        )
    session_id = resp1.json()["session_id"]

    with mock_claude_response("Good question!"):
        resp2 = await client.post(
            "/api/tutor/socratic",
            headers=auth_headers,
            json={
                "content": "I still don't get it",
                "section": "Biological and Biochemical Foundations of Living Systems",
                "topic": "Biochemistry",
                "concept": "Enzyme Kinetics",
                "session_id": session_id,
            },
        )
    assert resp2.status_code == 200
    assert resp2.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_socratic_escalation_increases(client, auth_headers):
    """Send multiple messages and verify escalation increases."""
    levels = []
    session_id = None

    for i in range(5):
        payload = {
            "content": f"Message {i}",
            "section": "Biological and Biochemical Foundations of Living Systems",
            "topic": "Biochemistry",
            "concept": "Enzyme Kinetics",
        }
        if session_id:
            payload["session_id"] = session_id

        with mock_claude_response(f"Response {i}"):
            resp = await client.post(
                "/api/tutor/socratic", headers=auth_headers, json=payload
            )
        data = resp.json()
        session_id = data["session_id"]
        levels.append(data["escalation_level"])

    # Escalation should not decrease
    for i in range(1, len(levels)):
        assert levels[i] >= levels[i - 1]
    # Should have reached at least level 2 after 5 messages
    assert max(levels) >= 2


@pytest.mark.asyncio
async def test_socratic_invalid_session(client, auth_headers):
    with mock_claude_response("test"):
        resp = await client.post(
            "/api/tutor/socratic",
            headers=auth_headers,
            json={
                "content": "test",
                "section": "S",
                "topic": "T",
                "concept": "C",
                "session_id": 99999,
            },
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_socratic_requires_auth(client):
    resp = await client.post(
        "/api/tutor/socratic",
        json={
            "content": "test",
            "section": "S",
            "topic": "T",
            "concept": "C",
        },
    )
    assert resp.status_code == 401
