from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


LearningRoadmapStatus = Literal["partial", "missing"]
LearningRoadmapPriority = Literal["high", "medium", "low"]
LearningRoadmapProgressStatus = Literal[
    "not_started",
    "in_progress",
    "completed",
]




class LearningRoadmapItem(BaseModel):
    """One deterministic learning recommendation derived from a skill gap."""

    id: int
    skill: str
    status: LearningRoadmapStatus
    priority: LearningRoadmapPriority
    reason: str
    progress_status: LearningRoadmapProgressStatus
    minimum_hours: int | None = Field(default=None, ge=1)
    maximum_hours: int | None = Field(default=None, ge=1)
    effort_available: bool = False

    @model_validator(mode="after")
    def validate_effort(self)->"LearningRoadmapItem":
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


class JobLearningRoadmapResponse(BaseModel):
    """Learning roadmap for a resume and target job."""

    resume_id: int
    job_id: int
    total_items: int = Field(ge=0)
    total_minimum_hours: int = Field(default=0, ge=0)
    total_maximum_hours: int = Field(default=0, ge=0)
    effort_available_items: int = Field(default=0, ge=0)
    effort_unavailable_items: int = Field(default=0, ge=0)
    roadmap: list[LearningRoadmapItem] = Field(
        default_factory=list,
    )


class LearningRoadmapProgressUpdate(BaseModel):
    """Request body for changing roadmap-item progress."""

    progress_status: LearningRoadmapProgressStatus


class LearningRoadmapProgressResponse(BaseModel):
    """Updated roadmap-item progress response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    skill: str
    progress_status: LearningRoadmapProgressStatus