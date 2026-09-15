from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.interview_evaluation import InterviewEvaluationResponse
from app.services.interview_evaluation_service import (
    InterviewAnswerNotFoundError,
    InterviewSessionNotFoundError,
)
from app.api import interview_evaluation as evaluation_api


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def evaluation_response() -> InterviewEvaluationResponse:
    return InterviewEvaluationResponse(
        session_id=1,
        answer_id=2,
        relevance_score=80.0,
        completeness_score=75.0,
        technical_score=90.0,
        overall_score=82.5,
        strengths=["The answer is relevant."],
        improvements=["Explain the trade-offs."],
    )


def test_llm_evaluation_returns_200_and_response_model(
    client,
    monkeypatch,
):
    expected = evaluation_response()
    captured = {}

    def fake_evaluate_answer_with_llm(**kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(
        evaluation_api,
        "evaluate_answer_with_llm",
        fake_evaluate_answer_with_llm,
    )

    response = client.post(
        "/interview-sessions/1/answers/2/evaluate-llm"
    )

    assert response.status_code == 200
    assert response.json() == expected.model_dump()
    assert captured["session_id"] == 1
    assert captured["answer_id"] == 2
    assert "session" in captured


@pytest.mark.parametrize(
    "service_error",
    [
        InterviewSessionNotFoundError(
            "The requested interview session was not found."
        ),
        InterviewAnswerNotFoundError(
            "The requested answer was not found for this session."
        ),
    ],
)
def test_llm_evaluation_maps_missing_resources_to_404(
    client,
    monkeypatch,
    service_error,
):
    def fake_evaluate_answer_with_llm(**kwargs):
        raise service_error

    monkeypatch.setattr(
        evaluation_api,
        "evaluate_answer_with_llm",
        fake_evaluate_answer_with_llm,
    )

    response = client.post(
        "/interview-sessions/1/answers/2/evaluate-llm"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == str(service_error)


def test_deterministic_evaluation_endpoint_remains_separate(
    client,
    monkeypatch,
):
    expected = evaluation_response()
    deterministic_calls = []

    def fake_evaluate_answer(**kwargs):
        deterministic_calls.append(kwargs)
        return expected

    def fail_if_llm_called(**kwargs):
        pytest.fail(
            "The deterministic endpoint must not call the LLM evaluator."
        )

    monkeypatch.setattr(
        evaluation_api,
        "evaluate_answer",
        fake_evaluate_answer,
    )
    monkeypatch.setattr(
        evaluation_api,
        "evaluate_answer_with_llm",
        fail_if_llm_called,
    )

    response = client.post(
        "/interview-sessions/1/answers/2/evaluate"
    )

    assert response.status_code == 200
    assert response.json() == expected.model_dump()
    assert len(deterministic_calls) == 1