from pydantic import BaseModel, Field


class AIJobExplanationResponse(BaseModel):
    resume_id: int
    job_id: int
    hybrid_score: float = Field(ge=0.0, le=1.0)
    explanation: str