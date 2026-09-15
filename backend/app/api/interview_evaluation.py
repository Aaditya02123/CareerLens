from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.interview_evaluation import InterviewEvaluationResponse
from app.services.interview_evaluation_service import (
    InterviewAnswerNotFoundError,
    InterviewSessionNotFoundError,
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
    ResumeNotFoundError,
    evaluate_answer,
)

router = APIRouter(tags=["Interview Evaluation"])


@router.post(
    "/interview-sessions/{session_id}/answers/{answer_id}/evaluate",
    response_model=InterviewEvaluationResponse,
)
def evaluate_interview_answer(
    session_id: int,
    answer_id: int,
    db: Session = Depends(get_db),
) -> InterviewEvaluationResponse:
    """Generate a deterministic evaluation for an answer."""
    try:
        return evaluate_answer(
            session_id=session_id,
            answer_id=answer_id,
            session=db,
        )
    except (
        InterviewSessionNotFoundError,
        InterviewAnswerNotFoundError,
        ResumeAnalysisNotFoundError,
        ResumeNotFoundError,
        JobNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="The interview answer could not be evaluated.",
        ) from error