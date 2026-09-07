from pydantic import BaseModel, Field

from app.models.job_ranking import RankedJobMatch


class JobRecommendationResponse(BaseModel):
    """Personalized ranked job recommendations for a resume."""

    resume_id: int
    recommendations: list[RankedJobMatch] = Field(
        default_factory=list
    )