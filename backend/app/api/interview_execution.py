from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.interview_execution import (
    InterviewExecutionSessionResponse,
    InterviewSessionAnswerCreate,
)
from app.services.interview_execution_service import (
    EmptyInterviewBlueprintError,
    InterviewExecutionAnswerError,
    InterviewExecutionBlueprintNotFoundError,
    InterviewExecutionSessionNotFoundError,
    InterviewExecutionService,
    InvalidInterviewExecutionTransitionError,
)


router = APIRouter(tags=["Interview Sessions"])


@router.post(
    "/interview-preparation/blueprints/{blueprint_id}/sessions",
    response_model=InterviewExecutionSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_interview_execution_session(
    blueprint_id: int,
    db: Session = Depends(get_db),
) -> InterviewExecutionSessionResponse:
    try:
        return InterviewExecutionService(db).create_session(blueprint_id)
    except InterviewExecutionBlueprintNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except EmptyInterviewBlueprintError as error:
        raise HTTPException(422, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview session could not be created.",
        ) from error


@router.get(
    "/interview-preparation/sessions/{session_id}",
    response_model=InterviewExecutionSessionResponse,
)
def get_interview_execution_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> InterviewExecutionSessionResponse:
    try:
        return InterviewExecutionService(db).get_session(session_id)
    except InterviewExecutionSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview session could not be retrieved.",
        ) from error


@router.post(
    "/interview-preparation/sessions/{session_id}/start",
    response_model=InterviewExecutionSessionResponse,
)
def start_interview_execution_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> InterviewExecutionSessionResponse:
    try:
        return InterviewExecutionService(db).start_session(session_id)
    except InterviewExecutionSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except InvalidInterviewExecutionTransitionError as error:
        raise HTTPException(409, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview session could not be started.",
        ) from error


@router.post(
    "/interview-preparation/sessions/{session_id}/answers",
    response_model=InterviewExecutionSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_interview_execution_answer(
    session_id: int,
    answer_data: InterviewSessionAnswerCreate,
    db: Session = Depends(get_db),
) -> InterviewExecutionSessionResponse:
    try:
        return InterviewExecutionService(db).submit_answer(
            session_id=session_id,
            answer_data=answer_data,
        )
    except InterviewExecutionSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except (
        InterviewExecutionAnswerError,
        InvalidInterviewExecutionTransitionError,
    ) as error:
        raise HTTPException(422, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview answer could not be submitted.",
        ) from error
