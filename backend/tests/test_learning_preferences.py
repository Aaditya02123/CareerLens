from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.models.learning_preferences import (
    DEFAULT_PACE,
    DEFAULT_WEEKLY_HOURS,
    LearningPreferencesResponse,
    LearningPreferencesUpsert,
)
from app.services import learning_preferences_service as service_module
from app.services.learning_preferences_service import (
    LearningPreferencesUserNotFoundError,
    get_learning_preferences,
    save_learning_preferences,
)


class FakeUserRepository:
    user = object()

    def __init__(self, session):
        self.session = session

    def get_by_id(self, user_id):
        return type(self).user


class FakeLearningPreferencesRepository:
    saved = None
    create_calls = 0
    update_calls = 0

    def __init__(self, session):
        self.session = session

    def get_by_user_id(self, user_id):
        return type(self).saved

    def create(self, **values):
        type(self).create_calls += 1
        type(self).saved = SimpleNamespace(id=1, **values)
        return type(self).saved

    def update(self, preferences, **values):
        type(self).update_calls += 1
        for key, value in values.items():
            setattr(preferences, key, value)
        return preferences


@pytest.fixture(autouse=True)
def reset_fakes(monkeypatch):
    FakeUserRepository.user = object()
    FakeLearningPreferencesRepository.saved = None
    FakeLearningPreferencesRepository.create_calls = 0
    FakeLearningPreferencesRepository.update_calls = 0
    monkeypatch.setattr(
        service_module,
        "UserRepository",
        FakeUserRepository,
    )
    monkeypatch.setattr(
        service_module,
        "LearningPreferencesRepository",
        FakeLearningPreferencesRepository,
    )


def make_payload(**overrides):
    values = {
        "weekly_hours": 8,
        "target_completion_date": date.today() + timedelta(days=30),
        "pace": "balanced",
        "preferred_resource_types": ["official_docs", "practice"],
    }
    values.update(overrides)
    return LearningPreferencesUpsert(**values)


def test_get_returns_defaults_without_creating_a_record():
    result = get_learning_preferences(3, Mock())

    assert result == LearningPreferencesResponse(
        id=None,
        user_id=3,
        weekly_hours=DEFAULT_WEEKLY_HOURS,
        target_completion_date=None,
        pace=DEFAULT_PACE,
        preferred_resource_types=[],
        is_saved=False,
    )
    assert FakeLearningPreferencesRepository.create_calls == 0


def test_save_creates_preferences_on_first_write():
    result = save_learning_preferences(3, make_payload(), Mock())

    assert result.is_saved is True
    assert result.id == 1
    assert result.weekly_hours == 8
    assert result.preferred_resource_types == [
        "official_docs",
        "practice",
    ]
    assert FakeLearningPreferencesRepository.create_calls == 1


def test_save_updates_existing_preferences():
    FakeLearningPreferencesRepository.saved = SimpleNamespace(
        id=4,
        user_id=3,
        weekly_hours=4,
        target_completion_date=None,
        pace="flexible",
        preferred_resource_types=[],
    )

    result = save_learning_preferences(
        3,
        make_payload(weekly_hours=12, pace="intensive"),
        Mock(),
    )

    assert result.id == 4
    assert result.weekly_hours == 12
    assert result.pace == "intensive"
    assert FakeLearningPreferencesRepository.create_calls == 0
    assert FakeLearningPreferencesRepository.update_calls == 1


def test_missing_user_is_rejected():
    FakeUserRepository.user = None

    with pytest.raises(LearningPreferencesUserNotFoundError):
        get_learning_preferences(999, Mock())


@pytest.mark.parametrize("weekly_hours", [0, 169])
def test_weekly_hours_are_bounded(weekly_hours):
    with pytest.raises(ValidationError):
        make_payload(weekly_hours=weekly_hours)


def test_invalid_pace_is_rejected():
    with pytest.raises(ValidationError):
        make_payload(pace="sprint")


def test_unsupported_resource_type_is_rejected():
    with pytest.raises(ValidationError):
        make_payload(preferred_resource_types=["video"])


def test_duplicate_resource_types_are_rejected():
    with pytest.raises(ValidationError):
        make_payload(
            preferred_resource_types=["tutorial", "tutorial"],
        )


def test_past_target_date_is_rejected():
    with pytest.raises(ValidationError):
        make_payload(
            target_completion_date=date.today() - timedelta(days=1),
        )


def test_null_target_date_is_valid():
    payload = make_payload(target_completion_date=None)

    assert payload.target_completion_date is None
