from typing import Literal

from pydantic import BaseModel, Field


class LearningRoadmapItem(BaseModel):
    """One deterministic learning recommendation."""

    skill: str
    priority: Literal["high", "medium", "low"]
    reason: str


class JobLearningRoadmapResponse(BaseModel):
    """Learning roadmap for a resume and target job."""

    resume_id: int
    job_id: int
    total_missing_skills: int = Field(ge=0)
    roadmap: list[LearningRoadmapItem] = Field(
        default_factory=list
    )