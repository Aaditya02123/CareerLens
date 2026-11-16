from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api import adaptive_interview as api_module
from app.core.database import get_db
from app.main import app
from app.models.interview_execution import AdaptiveDecisionResponse
from app.services.adaptive_interview_service import (
    AdaptiveProviderError,
    AdaptiveQuestionError,
)
from app.services.interview_execution_service import (
    InterviewExecutionSessionNotFoundError,
)


@pytest.fixture
def client(monkeypatch) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_adaptive_decision_success(client, monkeypatch):
    class FakeService:
        def __init__(self, db):
            pass

        def decide_after_answer(self, **kwargs):
            return AdaptiveDecisionResponse(
                session_id=1,
                parent_question_id=2,
                outcome="continue",
                follow_up_question=None,
            )

    monkeypatch.setattr(api_module, "AdaptiveInterviewService", FakeService)
    response = client.post(
        "/interview-preparation/sessions/1/adaptive-decision",
        json={"parent_question_id": 2},
    )
    assert response.status_code == 200
    assert response.json()["outcome"] == "continue"


@pytest.mark.parametrize(
    ("exception", "expected_status"),
    [
        (InterviewExecutionSessionNotFoundError("missing"), 404),
        (AdaptiveQuestionError("invalid"), 422),
        (AdaptiveProviderError("bad provider"), 503),
        (SQLAlchemyError("internal"), 500),
    ],
)
def test_adaptive_decision_error_mapping(
    client,
    monkeypatch,
    exception,
    expected_status,
):
    class FakeService:
        def __init__(self, db):
            pass

        def decide_after_answer(self, **kwargs):
            raise exception

    monkeypatch.setattr(api_module, "AdaptiveInterviewService", FakeService)
    response = client.post(
        "/interview-preparation/sessions/1/adaptive-decision",
        json={"parent_question_id": 2},
    )
    assert response.status_code == expected_status
    if expected_status == 500:
        assert "internal" not in response.text
