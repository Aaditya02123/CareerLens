from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.interview_execution import (
    AdaptiveDecisionRequest,
    AdaptiveDecisionResponse,
)
from app.services.adaptive_interview_service import (
    AdaptiveProviderError,
    AdaptiveQuestionError,
    AdaptiveInterviewService,
)
from app.services.interview_execution_service import (
    InterviewExecutionSessionNotFoundError,
)
from app.services.llm.ollama_generator import (
    OllamaConfigurationError,
    OllamaProviderError,
)


router = APIRouter(tags=["Interview Sessions"])


@router.post(
    "/interview-preparation/sessions/{session_id}/adaptive-decision",
    response_model=AdaptiveDecisionResponse,
)
def request_adaptive_decision(
    session_id: int,
    request_data: AdaptiveDecisionRequest,
    db: Session = Depends(get_db),
) -> AdaptiveDecisionResponse:
    try:
        return AdaptiveInterviewService(db).decide_after_answer(
            session_id=session_id,
            parent_question_id=request_data.parent_question_id,
        )
    except InterviewExecutionSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except AdaptiveQuestionError as error:
        raise HTTPException(422, str(error)) from error
    except (AdaptiveProviderError, OllamaConfigurationError, OllamaProviderError) as error:
        raise HTTPException(
            503,
            "Adaptive interview generation is temporarily unavailable.",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The adaptive interview decision could not be persisted.",
        ) from error
