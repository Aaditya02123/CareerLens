from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_owned_execution_session
from app.models.interview_model_answer import ModelAnswerResponse
from app.models.interview_proctoring import (
    ProctoringEventCreate,
    ProctoringEventResponse,
    ProctoringSummaryResponse,
)
from app.models.user import User
from app.services.interview_execution_service import (
    InterviewExecutionAnswerError,
    InterviewExecutionSessionNotFoundError,
)
from app.services.interview_model_answer_service import (
    InterviewModelAnswerService,
)
from app.services.interview_proctoring_service import (
    InterviewProctoringService,
)
from app.services.interview_roadmap_service import (
    InterviewRoadmapSyncService,
)

router = APIRouter(tags=["Interview Proctoring & Coaching"])


@router.post(
    "/interview-preparation/sessions/{session_id}/proctoring-events",
    response_model=ProctoringEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_proctoring_event(
    session_id: int,
    payload: ProctoringEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProctoringEventResponse:
    try:
        require_owned_execution_session(session_id, current_user, db)
        return InterviewProctoringService(db).record_event(session_id, payload)
    except HTTPException:
        raise
    except InterviewExecutionSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500, "Failed to record interview proctoring event."
        ) from error


@router.get(
    "/interview-preparation/sessions/{session_id}/proctoring-summary",
    response_model=ProctoringSummaryResponse,
)
def get_proctoring_summary(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProctoringSummaryResponse:
    try:
        require_owned_execution_session(session_id, current_user, db)
        return InterviewProctoringService(db).get_summary(session_id)
    except HTTPException:
        raise
    except InterviewExecutionSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500, "Failed to retrieve proctoring summary."
        ) from error


@router.post(
    "/interview-preparation/sessions/{session_id}/answers/{answer_id}/model-answer",
    response_model=ModelAnswerResponse,
)
def get_model_answer_comparison(
    session_id: int,
    answer_id: int,
    duration_seconds: float | None = Query(None, ge=1.0, le=600.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelAnswerResponse:
    try:
        require_owned_execution_session(session_id, current_user, db)
        return InterviewModelAnswerService(db).generate_for_answer(
            session_id=session_id,
            answer_id=answer_id,
            duration_seconds=duration_seconds,
        )
    except HTTPException:
        raise
    except InterviewExecutionSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except InterviewExecutionAnswerError as error:
        raise HTTPException(404, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500, "Failed to generate exemplar answer comparison."
        ) from error


@router.post(
    "/interview-preparation/sessions/{session_id}/sync-roadmap",
    status_code=status.HTTP_200_OK,
)
def sync_interview_gaps_to_roadmap(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, int | str | list[str]]:
    try:
        require_owned_execution_session(session_id, current_user, db)
        return InterviewRoadmapSyncService(db).sync_gaps_to_roadmap(session_id)
    except HTTPException:
        raise
    except InterviewExecutionSessionNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500, "Failed to sync interview gaps to learning roadmap."
        ) from error
