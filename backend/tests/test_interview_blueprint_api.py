from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api import interview_blueprints as api_module
from app.core.database import get_db
from app.main import app
from app.models.interview_blueprint import InterviewBlueprintResponse
from app.services.interview_blueprint_service import (
    BlueprintResumeNotFoundError,
    InterviewBlueprintNotFoundError,
)


@pytest.fixture
def client(monkeypatch) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_blueprint_maps_missing_resume_to_404(client, monkeypatch):
    def fake_generate(**kwargs):
        raise BlueprintResumeNotFoundError("Resume not found.")

    monkeypatch.setattr(api_module, "generate_interview_blueprint", fake_generate)
    response = client.post(
        "/interview-preparation/resumes/1/jobs/2/blueprint",
        json={"question_count": 2},
    )
    assert response.status_code == 404


def test_create_blueprint_returns_structured_response(client, monkeypatch):
    expected = InterviewBlueprintResponse(
        id=1,
        resume_id=2,
        job_id=3,
        target_role="Backend Engineer",
        interview_type="mixed",
        difficulty="adaptive",
        duration_minutes=30,
        question_count=1,
        created_at=datetime.now(timezone.utc),
        competencies=[],
        questions=[],
        rubric=[],
    )
    monkeypatch.setattr(
        api_module,
        "generate_interview_blueprint",
        lambda **kwargs: expected,
    )

    response = client.post(
        "/interview-preparation/resumes/2/jobs/3/blueprint",
        json={"question_count": 1},
    )
    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["question_count"] == 1


def test_get_blueprint_returns_404_when_missing(client, monkeypatch):
    def fake_get(*args):
        raise InterviewBlueprintNotFoundError("Blueprint not found.")

    monkeypatch.setattr(api_module, "get_interview_blueprint", fake_get)
    response = client.get("/interview-preparation/blueprints/999")
    assert response.status_code == 404


def test_create_blueprint_maps_database_error_to_500(client, monkeypatch):
    def fake_generate(**kwargs):
        raise SQLAlchemyError("internal details")

    monkeypatch.setattr(api_module, "generate_interview_blueprint", fake_generate)
    response = client.post(
        "/interview-preparation/resumes/1/jobs/2/blueprint",
        json={},
    )
    assert response.status_code == 500
    assert "internal details" not in response.text
