from pydantic import BaseModel, Field


class SemanticMatchResult(BaseModel):
    """Semantic similarity between a persisted resume analysis and a job."""

    resume_id: int
    job_id: int

    cosine_similarity: float = Field(
        ge=-1.0,
        le=1.0,
    )

    semantic_score: float = Field(
        ge=0.0,
        le=1.0,
    )