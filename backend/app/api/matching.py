from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.matching import MatchResult
from app.services.matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
    calculate_match,
)

router = APIRouter()


@router.get(
    "/matching/resumes/{resume_id}/jobs/{job_id}",
    response_model=MatchResult,
)
def match_resume_to_job(
    resume_id: int,
    job_id: int,
    db: Session = Depends(get_db),
) -> MatchResult:
    """Calculate a deterministic resume-to-job skill match."""
    try:
        return calculate_match(
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
            detail="The match could not be calculated.",
        ) from error