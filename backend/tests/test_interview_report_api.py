from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api import interview_report as report_api
from app.core.database import get_db
from app.main import app
from app.models.interview_report import (
    InterviewCategoryScore,
    InterviewSessionReport,
)
from app.services.interview_evaluation_service import (
    InterviewSessionNotFoundError,
)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def make_report() -> InterviewSessionReport:
    return InterviewSessionReport(
        session_id=1,
        total_questions=2,
        answered_questions=2,
        average_relevance_score=75.0,
        average_completeness_score=65.0,
        average_technical_score=50.0,
        overall_score=70.0,
        category_scores={
            "technical": InterviewCategoryScore(
                average_overall_score=80.0,
                answer_count=1,
            ),
            "resume_based": InterviewCategoryScore(),
            "behavioral": InterviewCategoryScore(
                average_overall_score=60.0,
                answer_count=1,
            ),
            "job_specific": InterviewCategoryScore(),
        },
        strengths=["The answers were relevant."],
        improvements=["Add more detail."],
    )


def test_report_endpoint_returns_200_and_expected_structure(
    client,
    monkeypatch,
):
    expected_report = make_report()
    captured = {}

    def fake_generate_report(**kwargs):
        captured.update(kwargs)
        return expected_report

    monkeypatch.setattr(
        report_api,
        "generate_interview_session_report",
        fake_generate_report,
    )

    response = client.get(
        "/interview-sessions/1/report"
    )

    assert response.status_code == 200
    assert response.json() == expected_report.model_dump()
    assert captured["session_id"] == 1
    assert "session" in captured


def test_missing_session_maps_to_404(
    client,
    monkeypatch,
):
    error = InterviewSessionNotFoundError(
        "The requested interview session was not found."
    )

    def fake_generate_report(**kwargs):
        raise error

    monkeypatch.setattr(
        report_api,
        "generate_interview_session_report",
        fake_generate_report,
    )

    response = client.get(
        "/interview-sessions/999/report"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == str(error)


def test_report_endpoint_delegates_to_report_service(
    client,
    monkeypatch,
):
    calls = []

    def fake_generate_report(**kwargs):
        calls.append(kwargs)
        return make_report()

    monkeypatch.setattr(
        report_api,
        "generate_interview_session_report",
        fake_generate_report,
    )

    response = client.get(
        "/interview-sessions/7/report"
    )

    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0]["session_id"] == 7
    assert "session" in calls[0]