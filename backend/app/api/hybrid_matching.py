from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.hybrid_matching import HybridMatchResult
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
    calculate_hybrid_match,
)

router = APIRouter()


@router.get(
    "/hybrid-matching/resumes/{resume_id}/jobs/{job_id}",
    response_model=HybridMatchResult,
)
def hybrid_match_resume_to_job(
    resume_id: int,
    job_id: int,
    db: Session = Depends(get_db),
) -> HybridMatchResult:
    """Calculate a hybrid resume-to-job match."""
    try:
        return calculate_hybrid_match(
            resume_id=resume_id,
            job_id=job_id,
            session=db,
        )
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
            detail="The hybrid match could not be calculated.",
        ) from error