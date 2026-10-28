from fastapi.testclient import TestClient

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