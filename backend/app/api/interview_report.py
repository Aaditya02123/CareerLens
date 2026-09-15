from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.interview_report import InterviewSessionReport
from app.services.interview_evaluation_service import (
    InterviewSessionNotFoundError,
)
from app.services.interview_report_service import (
    generate_interview_session_report,
)


router = APIRouter(tags=["Interview Reports"])


@router.get(
    "/interview-sessions/{session_id}/report",
    response_model=InterviewSessionReport,
)
def get_interview_session_report(
    session_id: int,
    db: Session = Depends(get_db),
) -> InterviewSessionReport:
    """Generate an on-demand deterministic report for an interview session."""
    try:
        return generate_interview_session_report(
            session_id=session_id,
            session=db,
        )
    except InterviewSessionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The interview session report could not be generated.",
        ) from error