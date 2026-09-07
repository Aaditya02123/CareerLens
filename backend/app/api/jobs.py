from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.jobs import JobCreate, JobResponse
from app.services.job_service import (
    JobDuplicateError,
    JobNotFoundError,
    JobService,
)

router = APIRouter()


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
) -> JobResponse:
    """Create a job posting."""
    service = JobService(db)

    try:
        job = service.create_job(job_data)
    except JobDuplicateError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A job with this source and source job ID already exists.",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The job could not be created.",
        ) from error

    return JobResponse.model_validate(job)


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
) -> JobResponse:
    """Retrieve a job by ID."""
    service = JobService(db)

    try:
        job = service.get_job(job_id)
    except JobNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return JobResponse.model_validate(job)


@router.get(
    "/jobs",
    response_model=list[JobResponse],
)
def list_jobs(
    title: str | None = None,
    location: str | None = None,
    experience_level: str | None = None,
    source: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[JobResponse]:
    """Return a filtered and paginated list of jobs."""
    service = JobService(db)

    try:
        jobs = service.list_jobs(
            title=title,
            location=location,
            experience_level=experience_level,
            source=source,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [
        JobResponse.model_validate(job)
        for job in jobs
    ]