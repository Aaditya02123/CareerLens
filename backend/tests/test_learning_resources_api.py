from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api import learning_resources as api_module
from app.data.learning_resource_catalog import get_learning_resources
from app.services.learning_preferences_service import (
    LearningPreferencesUserNotFoundError,
)

from app.main import app


client = TestClient(app)


def test_known_skill_returns_resources_and_count():
    response = client.get("/learning-resources/python")

    assert response.status_code == 200

    body = response.json()

    assert body["skill"] == "python"
    assert body["total_resources"] > 0
    assert body["total_resources"] == len(body["resources"])

    for resource in body["resources"]:
        assert resource["skill"] == "python"
        assert resource["id"]
        assert resource["title"]
        assert resource["url"]
        assert resource["provider"]
        assert resource["resource_type"]
        assert resource["level"]


def test_skill_path_supports_case_insensitive_lookup():
    response = client.get("/learning-resources/PyThOn")

    assert response.status_code == 200

    body = response.json()

    assert body["skill"] == "python"
    assert body["total_resources"] > 0
    assert body["total_resources"] == len(body["resources"])


def test_unknown_skill_returns_empty_successful_response():
    response = client.get(
        "/learning-resources/unknown-skill",
    )

    assert response.status_code == 200
    assert response.json() == {
        "skill": "unknown-skill",
        "total_resources": 0,
        "resources": [],
    }


def test_response_uses_learning_resource_contract():
    response = client.get("/learning-resources/fastapi")

    assert response.status_code == 200

    body = response.json()
    resource = body["resources"][0]

    assert set(resource) == {
        "id",
        "skill",
        "title",
        "url",
        "provider",
        "resource_type",
        "level",
    }
    assert body["total_resources"] == len(body["resources"])


def test_user_aware_endpoint_prioritizes_saved_resource_types(monkeypatch):
    resources = get_learning_resources("python")
    personalized = (resources[1], resources[0])
    mocked_service = Mock(return_value=personalized)
    monkeypatch.setattr(
        api_module,
        "get_learning_resources_for_user",
        mocked_service,
    )

    response = client.get("/users/3/learning-resources/PyThOn")

    assert response.status_code == 200
    body = response.json()
    assert body["skill"] == "python"
    assert [resource["id"] for resource in body["resources"]] == [
        resources[1].id,
        resources[0].id,
    ]
    assert body["total_resources"] == 2
    mocked_service.assert_called_once()
    assert mocked_service.call_args.kwargs["user_id"] == 3
    assert mocked_service.call_args.kwargs["skill"] == "PyThOn"
    assert mocked_service.call_args.kwargs["session"] is not None


def test_user_aware_endpoint_returns_empty_unknown_skill(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "get_learning_resources_for_user",
        Mock(return_value=()),
    )

    response = client.get("/users/3/learning-resources/unknown-skill")

    assert response.status_code == 200
    assert response.json() == {
        "skill": "unknown-skill",
        "total_resources": 0,
        "resources": [],
    }


def test_user_aware_endpoint_maps_unknown_user_to_404(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "get_learning_resources_for_user",
        Mock(
            side_effect=LearningPreferencesUserNotFoundError(
                "missing user"
            )
        ),
    )

    response = client.get("/users/999/learning-resources/python")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "The specified user was not found."
    )


def test_user_aware_endpoint_maps_database_errors_to_500(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "get_learning_resources_for_user",
        Mock(side_effect=SQLAlchemyError("database failure")),
    )

    response = client.get("/users/3/learning-resources/python")

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Learning resources could not be loaded."
    )
