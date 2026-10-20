from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


LearningRoadmapStatus = Literal["partial", "missing"]
LearningRoadmapPriority = Literal["high", "medium", "low"]
LearningRoadmapProgressStatus = Literal[
    "not_started",
    "in_progress",
    "completed",
]


class LearningRoadmapItem(BaseModel):
    """One deterministic learning recommendation derived from a skill gap."""

    skill: str
    status: LearningRoadmapStatus
    priority: LearningRoadmapPriority
    reason: str


class JobLearningRoadmapResponse(BaseModel):
    """Learning roadmap for a resume and target job."""

    resume_id: int
    job_id: int
    total_items: int = Field(ge=0)
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