from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job_ranking import JobRankingResponse
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)
from app.services.job_ranking_service import rank_jobs_for_resume

router = APIRouter()


@router.get(
    "/matching/resumes/{resume_id}/jobs",
    response_model=JobRankingResponse,
)
def get_ranked_jobs(
    resume_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> JobRankingResponse:
    """Return jobs ranked by hybrid match score."""
    try:
        return rank_jobs_for_resume(
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
            detail="The job ranking could not be calculated.",
        ) from error