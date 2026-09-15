from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.interview_session import (
    InterviewAnswerCreate,
    InterviewAnswerResponse,
    InterviewSessionCreate,
    InterviewSessionResponse,
    InterviewSessionStatus,
)
from app.services.interview_session_service import (
    InactiveInterviewSessionError,
    InterviewSessionNotFoundError,
    InterviewSessionService,
    JobNotFoundError,
    ResumeNotFoundError,
    ResumeOwnershipError,
    UserNotFoundError,
)

router = APIRouter(tags=["Interview Sessions"])


class InterviewSessionStatusUpdate(BaseModel):
    """Request schema for updating an interview session status."""

    status: InterviewSessionStatus


@router.post(
    "/interview-sessions",
    response_model=InterviewSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_interview_session(
    session_data: InterviewSessionCreate,
    db: Session = Depends(get_db),
) -> InterviewSessionResponse:
    """Create an active interview session."""
    service = InterviewSessionService(db)

    try:
        interview_session = service.create_session(session_data)
    except (
        UserNotFoundError,
        ResumeNotFoundError,
        JobNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ResumeOwnershipError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The interview session could not be created.",
        ) from error

    return InterviewSessionResponse.model_validate(interview_session)


@router.get(
    "/interview-sessions/{session_id}",
    response_model=InterviewSessionResponse,
)
def get_interview_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> InterviewSessionResponse:
    """Return an interview session and its answers."""
    service = InterviewSessionService(db)

    try:
        interview_session = service.get_session(session_id)
    except InterviewSessionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The interview session could not be retrieved.",
        ) from error

    return InterviewSessionResponse.model_validate(interview_session)


@router.get(
    "/users/{user_id}/interview-sessions",
    response_model=list[InterviewSessionResponse],
)
def list_user_interview_sessions(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[InterviewSessionResponse]:
    """Return all interview sessions for a user."""
    service = InterviewSessionService(db)

    try:
        interview_sessions = service.list_sessions_for_user(user_id)
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The interview sessions could not be retrieved.",
        ) from error

    return [
        InterviewSessionResponse.model_validate(interview_session)
        for interview_session in interview_sessions
    ]


@router.patch(
    "/interview-sessions/{session_id}/status",
    response_model=InterviewSessionResponse,
)
def update_interview_session_status(
    session_id: int,
    status_data: InterviewSessionStatusUpdate,
    db: Session = Depends(get_db),
) -> InterviewSessionResponse:
    """Update an interview session status."""
    service = InterviewSessionService(db)

    try:
        interview_session = service.update_session_status(
            session_id=session_id,
            new_status=status_data.status,
        )
    except InterviewSessionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The interview session status could not be updated.",
        ) from error

    return InterviewSessionResponse.model_validate(interview_session)


@router.post(
    "/interview-sessions/{session_id}/answers",
    response_model=InterviewAnswerResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_interview_answer(
    session_id: int,
    answer_data: InterviewAnswerCreate,
    db: Session = Depends(get_db),
) -> InterviewAnswerResponse:
    """Submit a text answer for an active interview session."""
    service = InterviewSessionService(db)

    try:
        answer = service.submit_answer(
            session_id=session_id,
            answer_data=answer_data,
        )
    except InterviewSessionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except (InactiveInterviewSessionError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The interview answer could not be submitted.",
        ) from error

    return InterviewAnswerResponse.model_validate(answer)


@router.get(
    "/interview-sessions/{session_id}/answers",
    response_model=list[InterviewAnswerResponse],
)
def list_interview_answers(
    session_id: int,
    db: Session = Depends(get_db),
) -> list[InterviewAnswerResponse]:
    """Return all answers for an interview session."""
    service = InterviewSessionService(db)

    try:
        answers = service.list_answers(session_id)
    except InterviewSessionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The interview answers could not be retrieved.",
        ) from error

    return [
        InterviewAnswerResponse.model_validate(answer)
        for answer in answers
    ]