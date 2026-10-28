from app.data.learning_resource_catalog import (
    LearningResource,
    get_learning_resources as lookup_learning_resources,
)


def get_learning_resources_for_skill(
    skill: str,
) -> tuple[LearningResource, ...]:
    """Return curated learning resources for a skill."""
    return lookup_learning_resources(skill)