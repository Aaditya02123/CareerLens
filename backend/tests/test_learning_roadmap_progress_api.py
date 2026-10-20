from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api import learning_roadmap as api_module
from app.core.database import get_db
from app.main import app
from app.models.learning_roadmap import (
    JobLearningRoadmapResponse,
)


class FakeLearningRoadmapRepository:
    def __init__(
        self,
        *,
        item=None,
        update_error=None,
    ):
        self.item = item
        self.update_error = update_error

    def get_item_by_id(self, item_id: int):
        return self.item

    def update_item_progress(
        self,
        item,
        progress_status: str,
    ):
        if self.update_error is not None:
            raise self.update_error

        item.progress_status = progress_status
        return item


def make_item(progress_status="not_started"):
    return SimpleNamespace(
        id=10,
        skill="SQL",
        skill_gap_status="missing",
        priority="high",
        reason="SQL is missing from the resume.",
        progress_status=progress_status,
    )


@pytest.fixture
def client():
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = lambda: object()

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)


@pytest.mark.parametrize(
    "progress_status",
    [
        "in_progress",
        "completed",
        "not_started",
    ],
)
def test_successful_progress_update_returns_http_200(
    monkeypatch,
    client,
    progress_status,
):
    item = make_item()

    monkeypatch.setattr(
        api_module,
        "LearningRoadmapRepository",
        lambda session: FakeLearningRoadmapRepository(
            item=item,
        ),
    )

    response = client.patch(
        "/roadmaps/items/10/progress",
        json={"progress_status": progress_status},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 10,
        "skill": "SQL",
        "progress_status": progress_status,
    }

    assert item.skill_gap_status == "missing"
    assert item.priority == "high"
    assert item.reason == "SQL is missing from the resume."


def test_invalid_progress_status_returns_http_422(
    client,
):
    response = client.patch(
        "/roadmaps/items/10/progress",
        json={"progress_status": "paused"},
    )

    assert response.status_code == 422


def test_unknown_item_id_returns_http_404(
    monkeypatch,
    client,
):
    monkeypatch.setattr(
        api_module,
        "LearningRoadmapRepository",
        lambda session: FakeLearningRoadmapRepository(
            item=None,
        ),
    )

    response = client.patch(
        "/roadmaps/items/999/progress",
        json={"progress_status": "in_progress"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "The learning roadmap item was not found."
    )


def test_database_error_returns_http_500(
    monkeypatch,
    client,
):
    monkeypatch.setattr(
        api_module,
        "LearningRoadmapRepository",
        lambda session: FakeLearningRoadmapRepository(
            item=make_item(),
            update_error=SQLAlchemyError(
                "database failure"
            ),
        ),
    )

    response = client.patch(
        "/roadmaps/items/10/progress",
        json={"progress_status": "completed"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "The learning roadmap item could not be updated."
    )


def test_existing_roadmap_get_response_contract_is_unchanged(
    monkeypatch,
    client,
):
    expected = JobLearningRoadmapResponse(
        resume_id=5,
        job_id=1,
        total_items=1,
        roadmap=[],
    )

    mocked_builder = Mock(return_value=expected)

    monkeypatch.setattr(
        api_module,
        "build_learning_roadmap",
        mocked_builder,
    )

    response = client.get(
        "/roadmaps/resumes/5/jobs/1",
    )

    assert response.status_code == 200
    assert response.json() == {
        "resume_id": 5,
        "job_id": 1,
        "total_items": 1,
        "roadmap": [],
    }

    mocked_builder.assert_called_once()