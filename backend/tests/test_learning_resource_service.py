from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.data.learning_resource_catalog import (
    LearningResource,
    get_learning_resources,
)
from app.services import learning_resource_service as service_module
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


def test_saved_preferences_prioritize_matching_resource_types(monkeypatch):
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        Mock(
            return_value=SimpleNamespace(
                is_saved=True,
                preferred_resource_types=["practice"],
            )
        ),
    )

    resources = service_module.get_learning_resources_for_user(
        user_id=3,
        skill="python",
        session=Mock(),
    )

    assert [resource.resource_type for resource in resources] == [
        "practice",
        "official_docs",
    ]
    assert [resource.id for resource in resources] == [
        "python-exercism",
        "python-official-tutorial",
    ]


def test_empty_preferences_preserve_catalog_order(monkeypatch):
    original = get_learning_resources("python")
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        Mock(
            return_value=SimpleNamespace(
                is_saved=True,
                preferred_resource_types=[],
            )
        ),
    )

    resources = service_module.get_learning_resources_for_user(
        user_id=3,
        skill="python",
        session=Mock(),
    )

    assert resources == original


def test_unsaved_preferences_preserve_catalog_order(monkeypatch):
    original = get_learning_resources("python")
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        Mock(
            return_value=SimpleNamespace(
                is_saved=False,
                preferred_resource_types=["practice"],
            )
        ),
    )

    resources = service_module.get_learning_resources_for_user(
        user_id=3,
        skill="python",
        session=Mock(),
    )

    assert resources == original


def test_preference_groups_preserve_catalog_order(monkeypatch):
    monkeypatch.setattr(
        service_module,
        "get_learning_resources_for_skill",
        Mock(
            return_value=(
                LearningResource(
                    id="one",
                    skill="python",
                    title="One",
                    url="https://example.com/one",
                    provider="Example",
                    resource_type="official_docs",
                    level="beginner",
                ),
                LearningResource(
                    id="two",
                    skill="python",
                    title="Two",
                    url="https://example.com/two",
                    provider="Example",
                    resource_type="tutorial",
                    level="beginner",
                ),
                LearningResource(
                    id="three",
                    skill="python",
                    title="Three",
                    url="https://example.com/three",
                    provider="Example",
                    resource_type="official_docs",
                    level="intermediate",
                ),
            )
        ),
    )
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        Mock(
            return_value=SimpleNamespace(
                is_saved=True,
                preferred_resource_types=[
                    "official_docs",
                    "tutorial",
                ],
            )
        ),
    )

    resources = service_module.get_learning_resources_for_user(
        user_id=3,
        skill="python",
        session=Mock(),
    )

    assert [resource.id for resource in resources] == [
        "one",
        "three",
        "two",
    ]
    assert len({resource.id for resource in resources}) == 3


def test_no_matching_preference_preserves_catalog_order(monkeypatch):
    original = get_learning_resources("python")
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        Mock(
            return_value=SimpleNamespace(
                is_saved=True,
                preferred_resource_types=["course"],
            )
        ),
    )

    resources = service_module.get_learning_resources_for_user(
        user_id=3,
        skill="python",
        session=Mock(),
    )

    assert resources == original


def test_preferences_service_errors_are_preserved(monkeypatch):
    error = LookupError("missing user")
    monkeypatch.setattr(
        service_module,
        "get_learning_preferences",
        Mock(side_effect=error),
    )

    with pytest.raises(LookupError, match="missing user"):
        service_module.get_learning_resources_for_user(
            user_id=999,
            skill="python",
            session=Mock(),
        )
