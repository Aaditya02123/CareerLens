from typing import Literal

from pydantic import BaseModel, Field

from app.models.match_explaination import MatchEvidence


SkillGapStatus = Literal[
    "matched",
    "partial",
    "missing",
]

SkillGapPriority = Literal[
    "high",
    "medium",
    "low",
]


class SkillGapItem(BaseModel):
    """Deterministic classification of one required job skill."""

    skill: str
    status: SkillGapStatus
    evidence: list[MatchEvidence] = Field(
        default_factory=list,
    )
    reason: str
    priority: SkillGapPriority


class SkillGapResponse(BaseModel):
    """Explainable required-skill gap summary."""

    resume_id: int
    job_id: int
    total_required_skills: int = Field(
        ge=0,
    )
    matched_count: int = Field(
        ge=0,
    )
    partial_count: int = Field(
        ge=0,
    )
    missing_count: int = Field(
        ge=0,
    )
    matched: list[SkillGapItem] = Field(
        default_factory=list,
    )
    partial: list[SkillGapItem] = Field(
        default_factory=list,
    )
    missing: list[SkillGapItem] = Field(
        default_factory=list,
    )