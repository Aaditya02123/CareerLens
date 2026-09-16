from collections.abc import Generator
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.api import interview_sessions as interview_sessions_api
from app.services.interview_session_service import (
    InactiveInterviewSessionError,
    InterviewQuestionNotFoundError,
    InterviewQuestionOwnershipError,
)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class FakeInterviewSessionService:
    def __init__(self, session):
        pass

    def submit_answer(self, session_id, answer_data):
        if answer_data.question_id == 999:
            raise InterviewQuestionNotFoundError(
                "The specified interview question was not found."
            )

        if answer_data.question_id == 200:
            raise InterviewQuestionOwnershipError(
                "The question does not belong to the specified session."
            )

        if answer_data.question_id == 300:
            raise InactiveInterviewSessionError(
                "Answers can only be submitted to an active session."
            )

        return SimpleNamespace(
            id=50,
            session_id=session_id,
            question_id=answer_data.question_id,
            question="Persisted FastAPI question",
            answer=answer_data.answer,
            question_category="technical",
            created_at=datetime.now(timezone.utc),
        )


@pytest.fixture
def fake_service(monkeypatch):
    monkeypatch.setattr(
        interview_sessions_api,
        "InterviewSessionService",
        FakeInterviewSessionService,
    )


def test_valid_answer_uses_persisted_question_data(
    client,
    fake_service,
):
    response = client.post(
        "/interview-sessions/1/answers",
        json={
            "question_id": 100,
            "answer": "I would use FastAPI for the backend service.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["question_id"] == 100
    assert body["question"] == "Persisted FastAPI question"
    assert body["question_category"] == "technical"
    assert body["answer"] == (
        "I would use FastAPI for the backend service."
    )


def test_question_from_another_session_returns_400(
    client,
    fake_service,
):
    response = client.post(
        "/interview-sessions/2/answers",
        json={
            "question_id": 200,
            "answer": "Cross-session answer.",
        },
    )

    assert response.status_code == 400


def test_nonexistent_question_returns_404(
    client,
    fake_service,
):
    response = client.post(
        "/interview-sessions/1/answers",
        json={
            "question_id": 999,
            "answer": "Answer for a missing question.",
        },
    )

    assert response.status_code == 404


def test_inactive_session_rejects_answer_submission(
    client,
    fake_service,
):
    response = client.post(
        "/interview-sessions/1/answers",
        json={
            "question_id": 300,
            "answer": "Answer for an inactive session.",
        },
    )

    assert response.status_code == 400