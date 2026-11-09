from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api import learning_preferences as api_module
from app.core.database import get_db
from app.main import app
from app.services.learning_preferences_service import (
    LearningPreferencesUserNotFoundError,
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


def make_response(user_id=3, is_saved=True):
    return {
        "id": 1 if is_saved else None,
        "user_id": user_id,
        "weekly_hours": 8,
        "target_completion_date": str(
            date.today() + timedelta(days=30)
        ) if is_saved else None,
        "pace": "balanced",
        "preferred_resource_types": ["official_docs"],
        "is_saved": is_saved,
    }


def test_get_defaults_returns_http_200_without_saving(client, monkeypatch):
    expected = make_response(is_saved=False)
    mocked_service = Mock(return_value=expected)
    monkeypatch.setattr(
        api_module,
        "get_learning_preferences",
        mocked_service,
    )

    response = client.get(
        "/users/3/learning-preferences",
    )

    assert response.status_code == 200
    assert response.json() == expected
    mocked_service.assert_called_once()
    assert mocked_service.call_args.kwargs["user_id"] == 3
    assert mocked_service.call_args.kwargs["session"] is not None


def test_put_saves_preferences_and_returns_http_200(client, monkeypatch):
    expected = make_response()
    mocked_service = Mock(return_value=expected)
    monkeypatch.setattr(
        api_module,
        "save_learning_preferences",
        mocked_service,
    )

    payload = {
        "weekly_hours": 8,
        "target_completion_date": str(
            date.today() + timedelta(days=30)
        ),
        "pace": "balanced",
        "preferred_resource_types": ["official_docs"],
    }

    response = client.put(
        "/users/3/learning-preferences",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json() == expected
    assert mocked_service.call_args.kwargs["user_id"] == 3
    assert mocked_service.call_args.kwargs["payload"].weekly_hours == 8


def test_unknown_user_returns_http_404(client, monkeypatch):
    monkeypatch.setattr(
        api_module,
        "get_learning_preferences",
        Mock(
            side_effect=LearningPreferencesUserNotFoundError(
                "missing user"
            )
        ),
    )

    response = client.get(
        "/users/999/learning-preferences",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "The specified user was not found."
    )


def test_put_unknown_user_returns_http_404(client, monkeypatch):
    monkeypatch.setattr(
        api_module,
        "save_learning_preferences",
        Mock(
            side_effect=LearningPreferencesUserNotFoundError(
                "missing user"
            )
        ),
    )

    response = client.put(
        "/users/999/learning-preferences",
        json={
            "weekly_hours": 8,
            "target_completion_date": None,
            "pace": "balanced",
            "preferred_resource_types": [],
        },
    )

    assert response.status_code == 404


def test_invalid_request_returns_http_422(client):
    response = client.put(
        "/users/3/learning-preferences",
        json={
            "weekly_hours": 0,
            "pace": "balanced",
            "preferred_resource_types": [],
        },
    )

    assert response.status_code == 422


def test_database_error_returns_http_500(client, monkeypatch):
    monkeypatch.setattr(
        api_module,
        "get_learning_preferences",
        Mock(side_effect=SQLAlchemyError("database failure")),
    )

    response = client.get(
        "/users/3/learning-preferences",
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Learning preferences could not be loaded."
    )


def test_put_database_error_returns_http_500(client, monkeypatch):
    monkeypatch.setattr(
        api_module,
        "save_learning_preferences",
        Mock(side_effect=SQLAlchemyError("database failure")),
    )

    response = client.put(
        "/users/3/learning-preferences",
        json={
            "weekly_hours": 8,
            "target_completion_date": None,
            "pace": "balanced",
            "preferred_resource_types": [],
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Learning preferences could not be saved."
    )
