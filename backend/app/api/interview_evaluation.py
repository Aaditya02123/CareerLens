from fastapi import APIRouter, Depends, HTTPException, status
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
    evaluate_answer_with_llm,
)
from app.services.llm.providers import (
    LLMConfigurationError,
    LLMProviderError,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The interview answer could not be evaluated.",
        ) from error


@router.post(
    "/interview-sessions/{session_id}/answers/{answer_id}/evaluate-llm",
    response_model=InterviewEvaluationResponse,
)
def evaluate_interview_answer_with_llm(
    session_id: int,
    answer_id: int,
    db: Session = Depends(get_db),
) -> InterviewEvaluationResponse:
    """Generate an opt-in LLM evaluation for an answer."""
    try:
        return evaluate_answer_with_llm(
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except (LLMConfigurationError, LLMProviderError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The LLM interview evaluation could not be completed.",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The interview answer could not be evaluated.",
        ) from error