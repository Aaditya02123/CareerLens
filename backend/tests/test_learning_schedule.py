from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api import learning_schedule as api_module
from app.core.database import get_db
from app.main import app
from app.models.learning_preferences import (
    LearningPreferencesResponse,
)
from app.models.learning_roadmap import (
    JobLearningRoadmapResponse,
    LearningRoadmapItem,
)
from app.models.learning_schedule import LearningScheduleResponse
from app.services import learning_schedule_service as service_module
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)
from app.services.learning_schedule_service import (
    LearningRoadmapNotFoundError,
    ResumeNotFoundError,
    get_learning_schedule,
)


class FakeResumeRepository:
    resume = SimpleNamespace(id=5, user_id=7)

    def __init__(self, session):
        self.session = session

    def get_by_id(self, resume_id):
        return type(self).resume


class FakeJobRepository:
    job = SimpleNamespace(id=1)

    def __init__(self, session):
        self.session = session

    def get_by_id(self, job_id):
        return type(self).job


class FakePreferencesService:
    response = LearningPreferencesResponse(
        id=1,
        user_id=7,
        weekly_hours=10,
        target_completion_date=date.today() + timedelta(days=30),
        pace="balanced",
        preferred_resource_types=[],
        is_saved=True,
    )


@pytest.fixture(autouse=True)
def patch_repositories(monkeypatch):
    FakeResumeRepository.resume = SimpleNamespace(id=5, user_id=7)
    FakeJobRepository.job = SimpleNamespace(id=1)
    FakePreferencesService.response = LearningPreferencesResponse(
        id=1,
        user_id=7,
        weekly_hours=10,
        target_completion_date=(
            date.today() + timedelta(days=30)
        ),
        pace="balanced",
        preferred_resource_types=[],
        is_saved=True,
    )
    monkeypatch.setattr(
        service_module,
        "ResumeRepository",
        FakeResumeRepository,
    )
    monkeypatch.setattr(
        service_module,
        "JobRepository",
        FakeJobRepository,
    )
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        lambda **kwargs: FakePreferencesService.response,
    )


def make_item(
    item_id,
    skill,
    status="missing",
    progress_status="not_started",
):
    return LearningRoadmapItem(
        id=item_id,
        skill=skill,
        status=status,
        priority="high",
        reason=f"{skill} is needed.",
        progress_status=progress_status,
    )


def make_roadmap(items):
    return JobLearningRoadmapResponse(
        resume_id=5,
        job_id=1,
        total_items=len(items),
        roadmap=items,
    )


@pytest.fixture
def roadmap(monkeypatch):
    response = make_roadmap(
        [
            make_item(1, "SQL"),
            make_item(2, "Docker", progress_status="completed"),
        ]
    )
    monkeypatch.setattr(
        service_module,
        "build_learning_roadmap",
        Mock(return_value=response),
    )
    return response


def test_saved_preferences_calculate_remaining_hours_and_weeks(
    roadmap,
):
    result = get_learning_schedule(5, 1, Mock())

    assert result.configured is True
    assert result.weekly_hours == 10
    assert result.remaining_minimum_hours == 10
    assert result.remaining_maximum_hours == 16
    assert result.estimated_minimum_weeks == 1
    assert result.estimated_maximum_weeks == 2
    assert result.items[1].progress_status == "completed"


def test_default_preferences_do_not_create_a_record(
    monkeypatch,
    roadmap,
):
    defaults = LearningPreferencesResponse(
        id=None,
        user_id=7,
        weekly_hours=10,
        target_completion_date=None,
        pace="balanced",
        preferred_resource_types=[],
        is_saved=False,
    )
    mocked_preferences = Mock(return_value=defaults)
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        mocked_preferences,
    )

    result = get_learning_schedule(5, 1, Mock())

    assert result.configured is False
    assert result.schedule_status == "not_configured"
    mocked_preferences.assert_called_once()


@pytest.mark.parametrize(
    "progress_status, expected_minimum, expected_maximum",
    [
        ("completed", 0, 0),
        ("in_progress", 10, 16),
        ("not_started", 10, 16),
    ],
)
def test_progress_status_controls_remaining_effort(
    monkeypatch,
    progress_status,
    expected_minimum,
    expected_maximum,
):
    response = make_roadmap([
        make_item(1, "SQL", progress_status=progress_status),
    ])
    monkeypatch.setattr(
        service_module,
        "build_learning_roadmap",
        Mock(return_value=response),
    )

    result = get_learning_schedule(5, 1, Mock())

    assert result.remaining_minimum_hours == expected_minimum
    assert result.remaining_maximum_hours == expected_maximum


def test_unknown_effort_remains_visible_but_is_excluded(
    monkeypatch,
):
    response = make_roadmap([
        make_item(1, "Unknown Skill"),
        make_item(2, "Git"),
    ])
    monkeypatch.setattr(
        service_module,
        "build_learning_roadmap",
        Mock(return_value=response),
    )

    result = get_learning_schedule(5, 1, Mock())

    assert len(result.items) == 2
    assert result.items[0].effort_available is False
    assert result.items[0].minimum_hours is None
    assert result.remaining_minimum_hours == 4
    assert result.remaining_maximum_hours == 8


def test_target_date_on_track_and_at_risk(monkeypatch):
    response = make_roadmap([
        make_item(1, "Machine Learning"),
    ])
    monkeypatch.setattr(
        service_module,
        "build_learning_roadmap",
        Mock(return_value=response),
    )

    on_track_preferences = LearningPreferencesResponse(
        id=1,
        user_id=7,
        weekly_hours=10,
        target_completion_date=date.today() + timedelta(days=3),
        pace="balanced",
        preferred_resource_types=[],
        is_saved=True,
    )
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        Mock(return_value=on_track_preferences),
    )
    assert get_learning_schedule(5, 1, Mock()).schedule_status == "at_risk"

    at_risk_preferences = on_track_preferences.model_copy(
        update={
            "target_completion_date": date.today() + timedelta(days=100),
        }
    )
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        Mock(return_value=at_risk_preferences),
    )
    assert get_learning_schedule(5, 1, Mock()).schedule_status == "on_track"


def test_no_target_date_and_completed_roadmap(monkeypatch):
    response = make_roadmap([
        make_item(1, "SQL", progress_status="completed"),
    ])
    monkeypatch.setattr(
        service_module,
        "build_learning_roadmap",
        Mock(return_value=response),
    )
    preferences = FakePreferencesService.response.model_copy(
        update={"target_completion_date": None},
    )
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        Mock(return_value=preferences),
    )

    result = get_learning_schedule(5, 1, Mock())

    assert result.schedule_status == "completed"
    assert result.estimated_minimum_weeks == 0


def test_configured_schedule_without_target_date_has_no_target_status(
    monkeypatch,
):
    response = make_roadmap([
        make_item(1, "SQL"),
    ])
    monkeypatch.setattr(
        service_module,
        "build_learning_roadmap",
        Mock(return_value=response),
    )
    preferences = FakePreferencesService.response.model_copy(
        update={"target_completion_date": None},
    )
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        Mock(return_value=preferences),
    )

    result = get_learning_schedule(5, 1, Mock())

    assert result.schedule_status == "no_target_date"


def test_empty_roadmap_is_completed(monkeypatch):
    monkeypatch.setattr(
        service_module,
        "build_learning_roadmap",
        Mock(return_value=make_roadmap([])),
    )

    result = get_learning_schedule(5, 1, Mock())

    assert result.items == []
    assert result.schedule_status == "completed"
    assert result.remaining_minimum_hours == 0


@pytest.mark.parametrize(
    "repository, error",
    [
        (FakeResumeRepository, ResumeNotFoundError),
        (FakeJobRepository, JobNotFoundError),
    ],
)
def test_missing_resume_or_job_raises(
    monkeypatch,
    repository,
    error,
):
    if repository is FakeResumeRepository:
        FakeResumeRepository.resume = None
    else:
        FakeJobRepository.job = None

    with pytest.raises(error):
        get_learning_schedule(5, 1, Mock())


def test_missing_roadmap_raises(monkeypatch):
    monkeypatch.setattr(
        service_module,
        "build_learning_roadmap",
        Mock(return_value=None),
    )

    with pytest.raises(LearningRoadmapNotFoundError):
        get_learning_schedule(5, 1, Mock())


def test_mismatched_roadmap_is_rejected(monkeypatch):
    mismatched = make_roadmap([]).model_copy(
        update={"job_id": 999},
    )
    monkeypatch.setattr(
        service_module,
        "build_learning_roadmap",
        Mock(return_value=mismatched),
    )

    with pytest.raises(LearningRoadmapNotFoundError):
        get_learning_schedule(5, 1, Mock())


def test_resume_analysis_error_is_preserved(monkeypatch):
    monkeypatch.setattr(
        service_module,
        "build_learning_roadmap",
        Mock(side_effect=ResumeAnalysisNotFoundError("missing analysis")),
    )

    with pytest.raises(ResumeAnalysisNotFoundError):
        get_learning_schedule(5, 1, Mock())


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


def test_schedule_api_returns_http_200(
    monkeypatch,
    client,
):
    expected = LearningScheduleResponse(
        resume_id=5,
        job_id=1,
        configured=True,
        weekly_hours=10,
        target_completion_date=date.today() + timedelta(days=30),
        pace="balanced",
        remaining_minimum_hours=10,
        remaining_maximum_hours=16,
        estimated_minimum_weeks=1,
        estimated_maximum_weeks=2,
        schedule_status="on_track",
        items=[],
    )
    mocked_service = Mock(return_value=expected)
    monkeypatch.setattr(
        api_module,
        "get_learning_schedule",
        mocked_service,
    )

    response = client.get(
        "/roadmaps/resumes/5/jobs/1/schedule",
    )

    assert response.status_code == 200
    assert response.json()["schedule_status"] == "on_track"
    mocked_service.assert_called_once()


def test_schedule_api_maps_domain_not_found_to_404(
    monkeypatch,
    client,
):
    monkeypatch.setattr(
        api_module,
        "get_learning_schedule",
        Mock(side_effect=ResumeNotFoundError("missing resume")),
    )

    response = client.get(
        "/roadmaps/resumes/5/jobs/1/schedule",
    )

    assert response.status_code == 404


def test_schedule_api_maps_job_not_found_to_404(
    monkeypatch,
    client,
):
    monkeypatch.setattr(
        api_module,
        "get_learning_schedule",
        Mock(side_effect=JobNotFoundError("missing job")),
    )

    response = client.get(
        "/roadmaps/resumes/5/jobs/1/schedule",
    )

    assert response.status_code == 404


def test_schedule_api_maps_resume_analysis_error_to_404(
    monkeypatch,
    client,
):
    monkeypatch.setattr(
        api_module,
        "get_learning_schedule",
        Mock(side_effect=ResumeAnalysisNotFoundError("missing analysis")),
    )

    response = client.get(
        "/roadmaps/resumes/5/jobs/1/schedule",
    )

    assert response.status_code == 404


def test_schedule_api_maps_database_error_to_500(
    monkeypatch,
    client,
):
    monkeypatch.setattr(
        api_module,
        "get_learning_schedule",
        Mock(side_effect=SQLAlchemyError("database failure")),
    )

    response = client.get(
        "/roadmaps/resumes/5/jobs/1/schedule",
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "The learning schedule could not be calculated."
    )
