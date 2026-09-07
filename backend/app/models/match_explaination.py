from pydantic import BaseModel, Field


class MatchExplanationResponse(BaseModel):
    """Explainable deterministic summary of a hybrid match."""

    resume_id: int
    job_id: int

    hybrid_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    required_skill_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    preferred_skill_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    semantic_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    matched_required_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    matched_preferred_skills: list[str] = Field(default_factory=list)

    match_level: str

    skill_gap_count: int = Field(
        ge=0,
    )

    primary_factors: list[str] = Field(default_factory=list)