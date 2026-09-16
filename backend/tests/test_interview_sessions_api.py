from collections.abc import Generator
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import interview_sessions as api_module
from app.core.database import get_db
from app.main import app
from app.services.interview_session_service import (
    DuplicateInterviewAnswerError,
    InactiveInterviewSessionError,
    InterviewQuestionNotFoundError,
    InterviewQuestionOwnershipError,
)


class FakeService:
    def __init__(self, session):
        pass

    def submit_answer(self, session_id, answer_data):
        if answer_data.question_id == 999:
            raise InterviewQuestionNotFoundError("Question not found.")

        if answer_data.question_id == 200:
            raise InterviewQuestionOwnershipError(
                "The question does not belong to this session."
            )

        if answer_data.question_id == 300:
            raise InactiveInterviewSessionError(
                "Answers can only be submitted to an active session."
            )

        if answer_data.question_id == 400:
            raise DuplicateInterviewAnswerError(
                "This interview question already has an answer."
            )

        return SimpleNamespace(
            id=1,
            session_id=session_id,
            question_id=answer_data.question_id,
            question="Persisted question",
            answer=answer_data.answer,
            question_category="technical",
            created_at=datetime.now(timezone.utc),
        )


@pytest.fixture
def client(monkeypatch) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(
        api_module,
        "InterviewSessionService",
        FakeService,
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_first_answer_returns_201(client):
    response = client.post(
        "/interview-sessions/1/answers",
        json={
            "question_id": 100,
            "answer": "First answer.",
        },
    )

    assert response.status_code == 201


def test_duplicate_answer_returns_409(client):
    response = client.post(
        "/interview-sessions/1/answers",
        json={
            "question_id": 400,
            "answer": "Duplicate answer.",
        },
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    ("question_id", "expected_status"),
    [
        (999, 404),
        (200, 400),
        (300, 400),
    ],
)
def test_answer_errors_preserve_existing_http_mapping(
    client,
    question_id,
    expected_status,
):
    response = client.post(
        "/interview-sessions/1/answers",
        json={
            "question_id": question_id,
            "answer": "Answer.",
        },
    )

    assert response.status_code == expected_status