from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.skill_gap import SkillGapResponse
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)
from app.services.skill_gap_service import (
    get_skill_gap as build_skill_gap,
)


router = APIRouter()


@router.get(
    "/skill-gap/resumes/{resume_id}/jobs/{job_id}",
    response_model=SkillGapResponse,
)
def get_resume_job_skill_gap(
    resume_id: int,
    job_id: int,
    db: Session = Depends(get_db),
) -> SkillGapResponse:
    try:
        return build_skill_gap(
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
            detail="The skill gap could not be calculated.",
        ) from error