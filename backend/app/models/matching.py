from pydantic import BaseModel, Field


class MatchResult(BaseModel):
    """Deterministic skill match between a resume and a job."""

    job_id: int
    resume_id: int

    required_skill_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    preferred_skill_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    matched_required_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    matched_preferred_skills: list[str] = Field(default_factory=list)