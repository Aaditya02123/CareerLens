import pytest
from pydantic import ValidationError

from app.data.learning_resource_catalog import (
    LearningResource,
    get_learning_resources,
)
from app.models.learning_resource import (
    LearningResourceLookupResponse,
    LearningResourceResponse,
)


def test_resource_response_serializes_a_catalog_resource():
    resource = get_learning_resources("python")[0]

    response = LearningResourceResponse.model_validate(resource)

    assert response.id == resource.id
    assert response.skill == "python"
    assert response.title == resource.title
    assert response.url == resource.url
    assert response.provider == resource.provider
    assert response.resource_type == resource.resource_type
    assert response.level == resource.level


def test_lookup_response_serializes_resources_and_count():
    resources = get_learning_resources("fastapi")

    response = LearningResourceLookupResponse(
        skill="fastapi",
        total_resources=len(resources),
        resources=[
            LearningResourceResponse.model_validate(resource)
            for resource in resources
        ],
    )

    assert response.skill == "fastapi"
    assert response.total_resources == len(resources)
    assert len(response.resources) == len(resources)
    assert response.model_dump()["resources"][0]["skill"] == "fastapi"


def test_lookup_response_supports_empty_results():
    response = LearningResourceLookupResponse(
        skill="unknown skill",
        total_resources=0,
        resources=[],
    )

    assert response.total_resources == 0
    assert response.resources == []


def test_lookup_response_rejects_mismatched_resource_count():
    resource = LearningResourceResponse.model_validate(
        get_learning_resources("python")[0]
    )

    with pytest.raises(
        ValidationError,
        match="total_resources must equal",
    ):
        LearningResourceLookupResponse(
            skill="python",
            total_resources=0,
            resources=[resource],
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", ""),
        ("skill", ""),
        ("title", ""),
        ("url", ""),
        ("provider", ""),
    ],
)
def test_resource_response_rejects_empty_string_fields(field, value):
    values = {
        "id": "resource-1",
        "skill": "python",
        "title": "Python Tutorial",
        "url": "https://example.com/python",
        "provider": "Example",
        "resource_type": "tutorial",
        "level": "beginner",
    }
    values[field] = value

    with pytest.raises(ValidationError):
        LearningResourceResponse(**values)


def test_resource_response_rejects_invalid_resource_type():
    with pytest.raises(ValidationError):
        LearningResourceResponse(
            id="resource-1",
            skill="python",
            title="Python Tutorial",
            url="https://example.com/python",
            provider="Example",
            resource_type="video",
            level="beginner",
        )


def test_resource_response_rejects_invalid_level():
    with pytest.raises(ValidationError):
        LearningResourceResponse(
            id="resource-1",
            skill="python",
            title="Python Tutorial",
            url="https://example.com/python",
            provider="Example",
            resource_type="tutorial",
            level="expert",
        )


def test_lookup_response_rejects_negative_resource_count():
    with pytest.raises(ValidationError):
        LearningResourceLookupResponse(
            skill="python",
            total_resources=-1,
            resources=[],
        )


def test_learning_resource_dataclass_can_be_converted_from_attributes():
    resource = LearningResource(
        id="custom-python-resource",
        skill="python",
        title="Python Resource",
        url="https://example.com/python",
        provider="Example",
        resource_type="tutorial",
        level="beginner",
    )

    response = LearningResourceResponse.model_validate(resource)

    assert response.id == "custom-python-resource"
    assert response.skill == "python"