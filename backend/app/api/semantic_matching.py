from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.semantic_matching import SemanticMatchResult
from app.services.semantic_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
    calculate_semantic_match,
)

router = APIRouter()


@router.get(
    "/semantic-matching/resumes/{resume_id}/jobs/{job_id}",
    response_model=SemanticMatchResult,
)
def semantic_match_resume_to_job(
    resume_id: int,
    job_id: int,
    db: Session = Depends(get_db),
) -> SemanticMatchResult:
    """Calculate semantic similarity between a resume and job."""
    try:
        return calculate_semantic_match(
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
            detail="The semantic match could not be calculated.",
        ) from error