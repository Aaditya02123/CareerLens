from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job_recommendation import JobRecommendationResponse
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)
from app.services.job_recommendation_service import (
    recommend_jobs_for_resume,
)

router = APIRouter()


@router.get(
    "/recommendations/resumes/{resume_id}",
    response_model=JobRecommendationResponse,
)
def get_job_recommendations(
    resume_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> JobRecommendationResponse:
    """Return personalized job recommendations for a resume."""
    try:
        return recommend_jobs_for_resume(
            resume_id=resume_id,
            session=db,
            limit=limit,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except ResumeAnalysisNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except JobNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="The job recommendations could not be calculated.",
        ) from error