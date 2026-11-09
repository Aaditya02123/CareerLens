from sqlalchemy.orm import Session

from app.data.learning_resource_catalog import (
    LearningResource,
    get_learning_resources as lookup_learning_resources,
)
from app.services.learning_preferences_service import (
    get_learning_preferences,
)


def get_learning_resources_for_skill(
    skill: str,
) -> tuple[LearningResource, ...]:
    """Return curated learning resources for a skill."""
    return lookup_learning_resources(skill)


def _order_by_preferred_types(
    resources: tuple[LearningResource, ...],
    preferred_resource_types: list[str],
) -> tuple[LearningResource, ...]:
    """Prioritize preferred resource types while preserving stable order."""
    if not preferred_resource_types:
        return resources

    preference_order = {
        resource_type: index
        for index, resource_type in enumerate(preferred_resource_types)
    }
    fallback_rank = len(preference_order)

    ordered_resources = sorted(
        enumerate(resources),
        key=lambda indexed_resource: (
            preference_order.get(
                indexed_resource[1].resource_type,
                fallback_rank,
            ),
            indexed_resource[0],
        ),
    )

    return tuple(
        resource
        for _, resource in ordered_resources
    )


def get_learning_resources_for_user(
    user_id: int,
    skill: str,
    session: Session,
) -> tuple[LearningResource, ...]:
    """Return curated resources ordered by a user's saved preferences."""
    preferences = get_learning_preferences(
        user_id=user_id,
        session=session,
    )
    resources = get_learning_resources_for_skill(skill)

    if not preferences.is_saved:
        return resources

    return _order_by_preferred_types(
        resources,
        preferences.preferred_resource_types,
    )
