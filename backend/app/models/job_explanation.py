from pydantic import BaseModel, Field


class JobExplanationResult(BaseModel):
    resume_id: int
    job_id: int
    hybrid_score: float = Field(ge=0.0, le=1.0)
    why_it_fits: str
    gap: str
    next_step: str
    explanation: str


class AIJobExplanationResponse(BaseModel):
    resume_id: int
    job_id: int
    hybrid_score: float = Field(ge=0.0, le=1.0)

    # Retained for backward compatibility.
    explanation: str

    why_it_fits: str
    gap: str
    next_step: str