from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


LearningPace = Literal["flexible", "balanced", "intensive"]
LearningResourceType = Literal[
    "official_docs",
    "tutorial",
    "practice",
    "course",
]

DEFAULT_WEEKLY_HOURS = 10
DEFAULT_PACE: LearningPace = "balanced"
DEFAULT_PREFERRED_RESOURCE_TYPES: tuple[LearningResourceType, ...] = ()


def _validate_unique_resource_types(
    resource_types: list[LearningResourceType],
) -> list[LearningResourceType]:
    if len(resource_types) != len(set(resource_types)):
        raise ValueError(
            "preferred_resource_types must not contain duplicates."
        )

    return resource_types


def _validate_target_completion_date(
    target_completion_date: date | None,
) -> date | None:
    if target_completion_date is not None and target_completion_date < date.today():
        raise ValueError(
            "target_completion_date cannot be in the past."
        )

    return target_completion_date


class UserLearningPreferences(Base):
    """Persisted learning preferences belonging to one user."""

    __tablename__ = "user_learning_preferences"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_user_learning_preferences_user_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    weekly_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    target_completion_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    pace: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    preferred_resource_types: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="learning_preferences",
    )


class LearningPreferencesUpsert(BaseModel):
    """Request body for creating or replacing a user's preferences."""

    weekly_hours: int = Field(ge=1, le=168)
    target_completion_date: date | None = None
    pace: LearningPace = DEFAULT_PACE
    preferred_resource_types: list[LearningResourceType] = Field(
        default_factory=list,
    )

    _unique_resource_types = field_validator(
        "preferred_resource_types",
    )(_validate_unique_resource_types)
    _valid_target_date = field_validator(
        "target_completion_date",
    )(_validate_target_completion_date)


class LearningPreferencesResponse(BaseModel):
    """Saved or default learning preferences for one user."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    weekly_hours: int = Field(ge=1, le=168)
    target_completion_date: date | None = None
    pace: LearningPace
    preferred_resource_types: list[LearningResourceType] = Field(
        default_factory=list,
    )
    is_saved: bool

    _unique_resource_types = field_validator(
        "preferred_resource_types",
    )(_validate_unique_resource_types)
