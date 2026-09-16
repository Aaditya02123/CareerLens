from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.interview_session import (
    InterviewAnswerCreate,
    InterviewAnswerResponse,
    InterviewQuestionResponse,
    InterviewSessionCreate,
    InterviewSessionResponse,
    InterviewSessionStatus,
)
from app.services.hybrid_matching_service import (
    ResumeAnalysisNotFoundError,
)
from app.services.interview_session_service import (
    InactiveInterviewSessionError,
    InterviewQuestionNotFoundError,
    InterviewQuestionOwnershipError,
    InterviewSessionNotFoundError,
    InterviewSessionService,
    JobNotFoundError,
    ResumeNotFoundError,
    ResumeOwnershipError,
    UserNotFoundError,
)

router = APIRouter(tags=["Interview Sessions"])


class InterviewSessionStatusUpdate(BaseModel):
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
    try:
        result = InterviewSessionService(db).create_session(
            session_data
        )
    except (
        UserNotFoundError,
        ResumeNotFoundError,
        JobNotFoundError,
        ResumeAnalysisNotFoundError,
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

    return InterviewSessionResponse.model_validate(result)


@router.get(
    "/interview-sessions/{session_id}",
    response_model=InterviewSessionResponse,
)
def get_interview_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> InterviewSessionResponse:
    try:
        result = InterviewSessionService(db).get_session(session_id)
    except InterviewSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview session could not be retrieved.",
        ) from error

    return InterviewSessionResponse.model_validate(result)


@router.get(
    "/interview-sessions/{session_id}/questions",
    response_model=list[InterviewQuestionResponse],
)
def list_interview_questions(
    session_id: int,
    db: Session = Depends(get_db),
) -> list[InterviewQuestionResponse]:
    try:
        return InterviewSessionService(db).list_questions(session_id)
    except InterviewSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview questions could not be retrieved.",
        ) from error


@router.get(
    "/users/{user_id}/interview-sessions",
    response_model=list[InterviewSessionResponse],
)
def list_user_interview_sessions(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[InterviewSessionResponse]:
    try:
        sessions = InterviewSessionService(db).list_sessions_for_user(
            user_id
        )
    except UserNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview sessions could not be retrieved.",
        ) from error

    return [
        InterviewSessionResponse.model_validate(item)
        for item in sessions
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
    try:
        result = InterviewSessionService(db).update_session_status(
            session_id=session_id,
            new_status=status_data.status,
        )
    except InterviewSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview session status could not be updated.",
        ) from error

    return InterviewSessionResponse.model_validate(result)


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
    try:
        result = InterviewSessionService(db).submit_answer(
            session_id=session_id,
            answer_data=answer_data,
        )
    except InterviewSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except InterviewQuestionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except (
        InactiveInterviewSessionError,
        InterviewQuestionOwnershipError,
        ValueError,
    ) as error:
        raise HTTPException(400, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview answer could not be submitted.",
        ) from error

    return InterviewAnswerResponse.model_validate(result)


@router.get(
    "/interview-sessions/{session_id}/answers",
    response_model=list[InterviewAnswerResponse],
)
def list_interview_answers(
    session_id: int,
    db: Session = Depends(get_db),
) -> list[InterviewAnswerResponse]:
    try:
        answers = InterviewSessionService(db).list_answers(session_id)
    except InterviewSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview answers could not be retrieved.",
        ) from error

    return [
        InterviewAnswerResponse.model_validate(answer)
        for answer in answers
    ]