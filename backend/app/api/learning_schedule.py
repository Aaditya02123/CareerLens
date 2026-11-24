import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_owned_resume
from app.models.learning_schedule import LearningScheduleResponse
from app.models.user import User
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)
from app.services.learning_schedule_service import (
    LearningRoadmapNotFoundError,
    ResumeNotFoundError,
    get_learning_schedule,
)


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/roadmaps/resumes/{resume_id}/jobs/{job_id}/schedule",
    response_model=LearningScheduleResponse,
)
def read_learning_schedule(
    resume_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LearningScheduleResponse:
    """Return an indicative schedule projection for a roadmap."""
    try:
        require_owned_resume(resume_id, current_user, db)
        return get_learning_schedule(
            resume_id=resume_id,
            job_id=job_id,
            session=db,
        )
    except (
        ResumeNotFoundError,
        JobNotFoundError,
        ResumeAnalysisNotFoundError,
        LearningRoadmapNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        logger.exception(
            "Database error while loading schedule for resume_id=%s, "
            "job_id=%s",
            resume_id,
            job_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The learning schedule could not be calculated.",
        ) from error
