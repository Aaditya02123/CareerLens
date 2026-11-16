from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api import interview_evaluation_scorecard as api_module
from app.core.database import get_db
from app.main import app
from app.models.interview_scorecard import (
    AnswerEvaluationResponse,
    InterviewScorecardResponse,
)
from app.services.interview_evaluation_scorecard_service import (
    InterviewAnswerNotFoundForEvaluationError,
    InterviewEvaluationError,
    InterviewEvaluationProviderError,
)
from app.services.interview_execution_service import (
    InterviewExecutionSessionNotFoundError,
)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _evaluation_response() -> AnswerEvaluationResponse:
    now = datetime.now(timezone.utc)
    return AnswerEvaluationResponse(
        id=1,
        session_id=2,
        answer_id=3,
        question_id=4,
        competency_reference="Python",
        weighted_score=4.25,
        strengths=["Clear explanation"],
        improvement_areas=["Add a trade-off"],
        actionable_feedback=["Explain one failure case."],
        evaluation_status="complete",
        criteria=[],
        provider_name="FakeProvider",
        created_at=now,
        updated_at=now,
    )


def test_evaluate_answer_returns_201(client, monkeypatch):
    class FakeService:
        def __init__(self, db):
            pass

        def evaluate_answer(self, **kwargs):
            return _evaluation_response()

    monkeypatch.setattr(api_module, "InterviewEvaluationScorecardService", FakeService)
    response = client.post(
        "/interview-preparation/sessions/2/answers/3/evaluate"
    )

    assert response.status_code == 201
    assert response.json()["weighted_score"] == 4.25


@pytest.mark.parametrize(
    ("exception", "expected_status"),
    [
        (InterviewExecutionSessionNotFoundError("missing"), 404),
        (InterviewAnswerNotFoundForEvaluationError("missing"), 404),
        (InterviewEvaluationError("invalid state"), 409),
        (InterviewEvaluationProviderError("bad provider"), 503),
        (SQLAlchemyError("internal"), 500),
    ],
)
def test_evaluate_answer_error_mapping(
    client,
    monkeypatch,
    exception,
    expected_status,
):
    class FakeService:
        def __init__(self, db):
            pass

        def evaluate_answer(self, **kwargs):
            raise exception

    monkeypatch.setattr(api_module, "InterviewEvaluationScorecardService", FakeService)
    response = client.post(
        "/interview-preparation/sessions/2/answers/3/evaluate"
    )

    assert response.status_code == expected_status
    if expected_status == 500:
        assert "internal" not in response.text


def test_get_evaluation_and_scorecard(client, monkeypatch):
    evaluation = _evaluation_response()
    scorecard = InterviewScorecardResponse(
        session_id=2,
        status="complete",
        overall_score=4.25,
        evaluated_answer_count=1,
        pending_answer_ids=[],
        competency_scores=[],
        answer_evaluations=[evaluation],
        strengths=["Clear explanation"],
        improvement_areas=[],
    )

    class FakeService:
        def __init__(self, db):
            pass

        def get_answer_evaluation(self, **kwargs):
            return evaluation

        def get_scorecard(self, session_id):
            return scorecard

    monkeypatch.setattr(api_module, "InterviewEvaluationScorecardService", FakeService)
    evaluation_response = client.get(
        "/interview-preparation/sessions/2/answers/3/evaluation"
    )
    scorecard_response = client.get(
        "/interview-preparation/sessions/2/scorecard"
    )

    assert evaluation_response.status_code == 200
    assert evaluation_response.json()["answer_id"] == 3
    assert scorecard_response.status_code == 200
    assert scorecard_response.json()["session_id"] == 2
