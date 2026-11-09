from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.learning_preferences import LearningPace
from app.models.learning_roadmap import LearningRoadmapProgressStatus


LearningScheduleStatus = Literal[
    "not_configured",
    "no_estimate",
    "completed",
    "on_track",
    "at_risk",
    "no_target_date",
]


class LearningScheduleItem(BaseModel):
    """One roadmap item with its current schedule-relevant estimate."""

    roadmap_item_id: int
    skill: str = Field(min_length=1)
    progress_status: LearningRoadmapProgressStatus
    minimum_hours: int | None = Field(default=None, ge=1)
    maximum_hours: int | None = Field(default=None, ge=1)
    effort_available: bool

    @model_validator(mode="after")
    def validate_effort(self) -> "LearningScheduleItem":
        if self.effort_available:
            if (
                self.minimum_hours is None
                or self.maximum_hours is None
            ):
                raise ValueError(
                    "Available effort estimates require both hour values."
                )

            if self.minimum_hours > self.maximum_hours:
                raise ValueError(
                    "Minimum hours cannot exceed maximum hours."
                )
        elif (
            self.minimum_hours is not None
            or self.maximum_hours is not None
        ):
            raise ValueError(
                "Unavailable estimates must not contain hour values."
            )

        return self


class LearningScheduleResponse(BaseModel):
    """Indicative, non-persisted schedule projection for a roadmap."""

    resume_id: int
    job_id: int
    configured: bool
    weekly_hours: int = Field(ge=1, le=168)
    target_completion_date: date | None = None
    pace: LearningPace
    remaining_minimum_hours: int = Field(ge=0)
    remaining_maximum_hours: int = Field(ge=0)
    estimated_minimum_weeks: int = Field(ge=0)
    estimated_maximum_weeks: int = Field(ge=0)
    schedule_status: LearningScheduleStatus
    items: list[LearningScheduleItem] = Field(default_factory=list)
