from datetime import date

from sqlalchemy.orm import Session

from app.models.learning_preferences import (
    DEFAULT_PACE,
    DEFAULT_PREFERRED_RESOURCE_TYPES,
    DEFAULT_WEEKLY_HOURS,
    LearningPreferencesResponse,
    LearningPreferencesUpsert,
    UserLearningPreferences,
)
from app.repositories.learning_preferences_repository import (
    LearningPreferencesRepository,
)
from app.repositories.user_repository import UserRepository


class LearningPreferencesUserNotFoundError(LookupError):
    """Raised when preferences reference a missing user."""


def _ensure_user_exists(user_id: int, session: Session) -> None:
    if UserRepository(session).get_by_id(user_id) is None:
        raise LearningPreferencesUserNotFoundError(
            "The specified user was not found."
        )


def _default_response(user_id: int) -> LearningPreferencesResponse:
    return LearningPreferencesResponse(
        id=None,
        user_id=user_id,
        weekly_hours=DEFAULT_WEEKLY_HOURS,
        target_completion_date=None,
        pace=DEFAULT_PACE,
        preferred_resource_types=list(
            DEFAULT_PREFERRED_RESOURCE_TYPES,
        ),
        is_saved=False,
    )


def _response_from_saved(
    preferences: UserLearningPreferences,
) -> LearningPreferencesResponse:
    return LearningPreferencesResponse(
        id=preferences.id,
        user_id=preferences.user_id,
        weekly_hours=preferences.weekly_hours,
        target_completion_date=preferences.target_completion_date,
        pace=preferences.pace,
        preferred_resource_types=preferences.preferred_resource_types,
        is_saved=True,
    )


def get_learning_preferences(
    user_id: int,
    session: Session,
) -> LearningPreferencesResponse:
    """Return saved preferences or defaults without inserting a record."""
    _ensure_user_exists(user_id, session)

    preferences = LearningPreferencesRepository(session).get_by_user_id(
        user_id,
    )

    if preferences is None:
        return _default_response(user_id)

    return _response_from_saved(preferences)

def save_learning_preferences(
    user_id: int,
    payload: LearningPreferencesUpsert,
    session: Session,
) -> LearningPreferencesResponse:
    """Create or replace preferences for an existing user."""
    _ensure_user_exists(user_id, session)

    if (
        payload.target_completion_date is not None
        and payload.target_completion_date < date.today()
    ):
        raise ValueError(
            "target_completion_date cannot be in the past."
        )

    repository = LearningPreferencesRepository(session)
    preferences = repository.get_by_user_id(user_id)
    values = {
        "weekly_hours": payload.weekly_hours,
        "target_completion_date": payload.target_completion_date,
        "pace": payload.pace,
        "preferred_resource_types": list(
            payload.preferred_resource_types,
        ),
    }

    if preferences is None:
        preferences = repository.create(
            user_id=user_id,
            **values,
        )
    else:
        preferences = repository.update(
            preferences,
            **values,
        )

    return _response_from_saved(preferences)
