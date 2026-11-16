from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.interview_scorecard import (
    AnswerEvaluationResponse,
    InterviewScorecardResponse,
)
from app.services.interview_evaluation_scorecard_service import (
    InterviewAnswerNotFoundForEvaluationError,
    InterviewEvaluationError,
    InterviewEvaluationProviderError,
    InterviewEvaluationScorecardService,
    InterviewJobNotFoundError,
    InterviewResumeAnalysisNotFoundError,
)
from app.services.interview_execution_service import (
    InterviewExecutionSessionNotFoundError,
)
from app.services.llm.ollama_generator import (
    OllamaConfigurationError,
    OllamaProviderError,
)


router = APIRouter(tags=["Interview Evaluation"])


def _not_found(error: Exception) -> HTTPException:
    return HTTPException(status_code=404, detail=str(error))


@router.post(
    "/interview-preparation/sessions/{session_id}/answers/{answer_id}/evaluate",
    response_model=AnswerEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
def evaluate_interview_answer(
    session_id: int,
    answer_id: int,
    db: Session = Depends(get_db),
) -> AnswerEvaluationResponse:
    try:
        return InterviewEvaluationScorecardService(db).evaluate_answer(
            session_id=session_id,
            answer_id=answer_id,
        )
    except (
        InterviewExecutionSessionNotFoundError,
        InterviewAnswerNotFoundForEvaluationError,
        InterviewResumeAnalysisNotFoundError,
        InterviewJobNotFoundError,
    ) as error:
        raise _not_found(error) from error
    except InterviewEvaluationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (
        InterviewEvaluationProviderError,
        OllamaConfigurationError,
        OllamaProviderError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail="Interview answer evaluation is temporarily unavailable.",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="The interview answer evaluation could not be persisted.",
        ) from error


@router.get(
    "/interview-preparation/sessions/{session_id}/answers/{answer_id}/evaluation",
    response_model=AnswerEvaluationResponse,
)
def get_interview_answer_evaluation(
    session_id: int,
    answer_id: int,
    db: Session = Depends(get_db),
) -> AnswerEvaluationResponse:
    try:
        return InterviewEvaluationScorecardService(db).get_answer_evaluation(
            session_id=session_id,
            answer_id=answer_id,
        )
    except (
        InterviewExecutionSessionNotFoundError,
        InterviewAnswerNotFoundForEvaluationError,
    ) as error:
        raise _not_found(error) from error
    except InterviewEvaluationError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="The interview answer evaluation could not be retrieved.",
        ) from error


@router.get(
    "/interview-preparation/sessions/{session_id}/scorecard",
    response_model=InterviewScorecardResponse,
)
def get_interview_scorecard(
    session_id: int,
    db: Session = Depends(get_db),
) -> InterviewScorecardResponse:
    try:
        return InterviewEvaluationScorecardService(db).get_scorecard(session_id)
    except InterviewExecutionSessionNotFoundError as error:
        raise _not_found(error) from error
    except InterviewEvaluationError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="The interview scorecard could not be retrieved.",
        ) from error
