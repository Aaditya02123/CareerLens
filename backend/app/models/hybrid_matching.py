from pydantic import BaseModel, Field


class HybridMatchResult(BaseModel):
    """Combined deterministic and semantic resume-to-job match result."""

    resume_id: int
    job_id: int

    required_skill_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    semantic_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    preferred_skill_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    hybrid_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    required_skill_weight: float = Field(
        ge=0.0,
        le=1.0,
    )

    semantic_weight: float = Field(
        ge=0.0,
        le=1.0,
    )

    matched_required_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    matched_preferred_skills: list[str] = Field(default_factory=list)