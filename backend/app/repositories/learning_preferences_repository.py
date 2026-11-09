from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.learning_preferences import UserLearningPreferences


class LearningPreferencesRepository:
    """Database operations for user learning preferences."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_user_id(
        self,
        user_id: int,
    ) -> UserLearningPreferences | None:
        """Return saved preferences for a user, if present."""
        statement = select(UserLearningPreferences).where(
            UserLearningPreferences.user_id == user_id,
        )

        return self.session.scalar(statement)

    def create(
        self,
        *,
        user_id: int,
        weekly_hours: int,
        target_completion_date: date | None,
        pace: str,
        preferred_resource_types: list[str],
    ) -> UserLearningPreferences:
        """Create and persist a user's preferences."""
        preferences = UserLearningPreferences(
            user_id=user_id,
            weekly_hours=weekly_hours,
            target_completion_date=target_completion_date,
            pace=pace,
            preferred_resource_types=preferred_resource_types,
        )

        self.session.add(preferences)

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(preferences)
        return preferences
    def update(
        self,
        preferences: UserLearningPreferences,
        *,
        weekly_hours: int,
        target_completion_date: date | None,
        pace: str,
        preferred_resource_types: list[str],
    ) -> UserLearningPreferences:
        """Replace and persist a user's existing preferences."""
        preferences.weekly_hours = weekly_hours
        preferences.target_completion_date = target_completion_date
        preferences.pace = pace
        preferences.preferred_resource_types = preferred_resource_types

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(preferences)
        return preferences
