from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.match_explaination import MatchExplanationResponse
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)
from app.services.match_explaination_service import explain_match

router = APIRouter()


@router.get(
    "/matching/resumes/{resume_id}/jobs/{job_id}/explanation",
    response_model=MatchExplanationResponse,
)
def get_match_explanation(
    resume_id: int,
    job_id: int,
    db: Session = Depends(get_db),
) -> MatchExplanationResponse:
    """Return an explainable summary of a hybrid match."""
    try:
        return explain_match(
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
            detail="The match explanation could not be calculated.",
        ) from error