from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.learning_roadmap import JobLearningRoadmapResponse
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
) -> JobLearningRoadmapResponse:
    """Return a deterministic learning roadmap."""
    try:
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
        raise HTTPException(
            status_code=500,
            detail="The learning roadmap could not be calculated.",
        ) from error