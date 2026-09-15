from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.interview_preparation import InterviewPreparationResponse
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)
from app.services.interview_preparation_service import (
    build_interview_preparation,
)

router = APIRouter()


@router.get(
    "/interview-preparation/resumes/{resume_id}/jobs/{job_id}",
    response_model=InterviewPreparationResponse,
)
def get_interview_preparation(
    resume_id: int,
    job_id: int,
    db: Session = Depends(get_db),
) -> InterviewPreparationResponse:
    """Return deterministic interview preparation questions."""
    try:
        return build_interview_preparation(
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
            detail=(
                "The interview preparation could not be generated."
            ),
        ) from error