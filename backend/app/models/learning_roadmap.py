from typing import Literal

from pydantic import BaseModel, Field


LearningRoadmapStatus = Literal["partial", "missing"]
LearningRoadmapPriority = Literal["high", "medium", "low"]


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