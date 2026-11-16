from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api import interview_execution as api_module
from app.core.database import get_db
from app.main import app
from app.models.interview_execution import (
    InterviewExecutionSessionResponse,
    InterviewExecutionStatus,
)
from app.services.interview_execution_service import (
    EmptyInterviewBlueprintError,
    InterviewExecutionAnswerError,
    InterviewExecutionBlueprintNotFoundError,
    InterviewExecutionSessionNotFoundError,
    InvalidInterviewExecutionTransitionError,
)


@pytest.fixture
def client(monkeypatch) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _response():
    return InterviewExecutionSessionResponse(
        id=1,
        blueprint_id=4,
        status=InterviewExecutionStatus.CREATED,
        created_at=datetime.now(timezone.utc),
        started_at=None,
        completed_at=None,
        total_questions=1,
        answered_questions=0,
        remaining_questions=1,
        completion_percentage=0.0,
        current_question_position=1,
        next_question=None,
        answers=[],
    )


def test_create_session_returns_201(client, monkeypatch):
    class FakeService:
        def __init__(self, db):
            pass

        def create_session(self, blueprint_id):
            return _response()

    monkeypatch.setattr(api_module, "InterviewExecutionService", FakeService)
    response = client.post("/interview-preparation/blueprints/4/sessions")
    assert response.status_code == 201
    assert response.json()["status"] == "created"


@pytest.mark.parametrize(
    ("exception", "expected_status"),
    [
        (InterviewExecutionBlueprintNotFoundError("missing"), 404),
        (EmptyInterviewBlueprintError("empty"), 422),
        (SQLAlchemyError("internal"), 500),
    ],
)
def test_create_session_error_mapping(
    client,
    monkeypatch,
    exception,
    expected_status,
):
    class FakeService:
        def __init__(self, db):
            pass

        def create_session(self, blueprint_id):
            raise exception

    monkeypatch.setattr(api_module, "InterviewExecutionService", FakeService)
    response = client.post("/interview-preparation/blueprints/4/sessions")
    assert response.status_code == expected_status
    if expected_status == 500:
        assert "internal" not in response.text


def test_start_and_answer_error_mapping(client, monkeypatch):
    class FakeService:
        def __init__(self, db):
            pass

        def start_session(self, session_id):
            raise InvalidInterviewExecutionTransitionError("invalid")

        def submit_answer(self, session_id, answer_data):
            raise InterviewExecutionAnswerError("invalid answer")

    monkeypatch.setattr(api_module, "InterviewExecutionService", FakeService)
    assert client.post(
        "/interview-preparation/sessions/1/start"
    ).status_code == 409
    assert client.post(
        "/interview-preparation/sessions/1/answers",
        json={"answer": "text"},
    ).status_code == 422


def test_get_missing_session_maps_to_404(client, monkeypatch):
    class FakeService:
        def __init__(self, db):
            pass

        def get_session(self, session_id):
            raise InterviewExecutionSessionNotFoundError("missing")

    monkeypatch.setattr(api_module, "InterviewExecutionService", FakeService)
    assert client.get("/interview-preparation/sessions/1").status_code == 404
