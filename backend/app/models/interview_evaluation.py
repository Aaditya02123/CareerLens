from pydantic import BaseModel, Field


class InterviewEvaluationResponse(BaseModel):
    """Deterministic evaluation of one submitted interview answer."""

    session_id: int
    answer_id: int
    relevance_score: float = Field(ge=0.0, le=100.0)
    completeness_score: float = Field(ge=0.0, le=100.0)
    technical_score: float = Field(ge=0.0, le=100.0)
    overall_score: float = Field(ge=0.0, le=100.0)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)