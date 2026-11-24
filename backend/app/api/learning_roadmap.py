import logging

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_owned_resume, require_owned_roadmap_item
from app.models.learning_roadmap import (
    JobLearningRoadmapResponse,
    LearningRoadmapProgressResponse,
    LearningRoadmapProgressUpdate,
)
from app.models.user import User
from app.repositories.learning_roadmap_repository import (
    LearningRoadmapRepository,
)
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)
from app.services.learning_roadmap_service import build_learning_roadmap


router = APIRouter()


@router.get(
    "/roadmaps/resumes/{resume_id}/jobs/{job_id}",
    response_model=JobLearningRoadmapResponse,
)
def get_learning_roadmap(
    resume_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobLearningRoadmapResponse:
    """Return a deterministic learning roadmap."""
    try:
        require_owned_resume(resume_id, current_user, db)
        return build_learning_roadmap(
            resume_id=resume_id,
            job_id=job_id,
            session=db,
        )
    except ResumeAnalysisNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except JobNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        logger.exception(
            "Database error while building roadmap "
            "for resume_id=%s, job_id=%s",
            resume_id,
            job_id,
        )
        raise HTTPException(
            status_code=500,
            detail="The learning roadmap could not be calculated.",
        ) from error


@router.patch(
    "/roadmaps/items/{item_id}/progress",
    response_model=LearningRoadmapProgressResponse,
)
def update_learning_roadmap_item_progress(
    item_id: int,
    payload: LearningRoadmapProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LearningRoadmapProgressResponse:
    """Update only the progress status of a roadmap item."""
    repository = LearningRoadmapRepository(db)

    try:
        require_owned_roadmap_item(item_id, current_user, db)
        item = repository.get_item_by_id(item_id)

        if item is None:
            raise HTTPException(
                status_code=404,
                detail="The learning roadmap item was not found.",
            )

        updated_item = repository.update_item_progress(
            item=item,
            progress_status=payload.progress_status,
        )

        return LearningRoadmapProgressResponse.model_validate(
            updated_item,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="The learning roadmap item could not be updated.",
        ) from error
