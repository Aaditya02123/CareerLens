from sqlalchemy.orm import Session

from app.models.job_recommendation import JobRecommendationResponse
from app.services.job_ranking_service import rank_jobs_for_resume


def recommend_jobs_for_resume(
    resume_id: int,
    session: Session,
    limit: int = 10,
) -> JobRecommendationResponse:
    """Return the highest-ranked jobs for a resume."""
    if limit <= 0:
        raise ValueError("Limit must be greater than zero.")

    if limit > 100:
        raise ValueError("Limit cannot be greater than 100.")

    ranking_response = rank_jobs_for_resume(
        resume_id=resume_id,
        session=session,
        limit=limit,
    )

    return JobRecommendationResponse(
        resume_id=ranking_response.resume_id,
        recommendations=ranking_response.matches,
    )