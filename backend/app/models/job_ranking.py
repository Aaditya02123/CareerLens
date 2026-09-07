from pydantic import BaseModel, Field


class RankedJobMatch(BaseModel):
    """A hybrid match result with its ranking position."""

    rank: int = Field(ge=1)
    job_id: int
    resume_id: int

    hybrid_score: float = Field(ge=0.0, le=1.0)
    required_skill_score: float = Field(ge=0.0, le=1.0)
    semantic_score: float = Field(ge=0.0, le=1.0)
    preferred_skill_score: float = Field(ge=0.0, le=1.0)

    matched_required_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    matched_preferred_skills: list[str] = Field(default_factory=list)


class JobRankingResponse(BaseModel):
    """Ranked hybrid matches for a resume."""

    resume_id: int
    matches: list[RankedJobMatch] = Field(default_factory=list)