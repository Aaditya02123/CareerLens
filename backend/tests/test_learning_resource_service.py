from app.data.learning_resource_catalog import LearningResource, get_learning_resources
from app.services.learning_resource_service import (
    get_learning_resources_for_skill,
)


def test_known_skill_returns_curated_resources():
    resources = get_learning_resources_for_skill("python")

    assert isinstance(resources, tuple)
    assert resources
    assert resources == get_learning_resources("python")
    assert all(
        isinstance(resource, LearningResource)
        for resource in resources
    )


def test_skill_lookup_is_case_and_whitespace_insensitive():
    normalized = get_learning_resources_for_skill("python")
    varied_input = get_learning_resources_for_skill("  PyThOn  ")

    assert varied_input == normalized


def test_another_known_skill_returns_resources():
    resources = get_learning_resources_for_skill("SQL")

    assert resources
    assert all(resource.skill == "sql" for resource in resources)


def test_unknown_skill_returns_empty_tuple():
    resources = get_learning_resources_for_skill("unknown skill")

    assert resources == ()
    assert isinstance(resources, tuple)