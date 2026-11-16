from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.interview_blueprint import (
    InterviewBlueprintConfig,
    InterviewBlueprintResponse,
)
from app.services.interview_blueprint_service import (
    BlueprintJobDescriptionError,
    BlueprintJobNotFoundError,
    BlueprintResumeAnalysisNotFoundError,
    BlueprintResumeNotFoundError,
    InterviewBlueprintNotFoundError,
    InterviewBlueprintProviderError,
    delete_interview_blueprint,
    generate_interview_blueprint,
    get_interview_blueprint,
    list_interview_blueprints,
)
from app.services.llm.ollama_generator import (
    OllamaConfigurationError,
    OllamaProviderError,
)


router = APIRouter(tags=["Interview Blueprints"])


@router.post(
    "/interview-preparation/resumes/{resume_id}/jobs/{job_id}/blueprint",
    response_model=InterviewBlueprintResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_interview_blueprint(
    resume_id: int,
    job_id: int,
    config: InterviewBlueprintConfig | None = None,
    db: Session = Depends(get_db),
) -> InterviewBlueprintResponse:
    try:
        return generate_interview_blueprint(
            resume_id=resume_id,
            job_id=job_id,
            session=db,
            config=config,
        )
    except (
        BlueprintResumeNotFoundError,
        BlueprintJobNotFoundError,
        BlueprintResumeAnalysisNotFoundError,
        InterviewBlueprintNotFoundError,
    ) as error:
        raise HTTPException(404, str(error)) from error
    except BlueprintJobDescriptionError as error:
        raise HTTPException(400, str(error)) from error
    except (InterviewBlueprintProviderError, OllamaConfigurationError, OllamaProviderError) as error:
        raise HTTPException(
            503,
            "Interview blueprint generation is temporarily unavailable.",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview blueprint could not be created.",
        ) from error


@router.get(
    "/interview-preparation/blueprints/{blueprint_id}",
    response_model=InterviewBlueprintResponse,
)
def retrieve_interview_blueprint(
    blueprint_id: int,
    db: Session = Depends(get_db),
) -> InterviewBlueprintResponse:
    try:
        return get_interview_blueprint(blueprint_id, db)
    except InterviewBlueprintNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview blueprint could not be retrieved.",
        ) from error


@router.get(
    "/interview-preparation/resumes/{resume_id}/blueprints",
    response_model=list[InterviewBlueprintResponse],
)
def list_resume_interview_blueprints(
    resume_id: int,
    job_id: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[InterviewBlueprintResponse]:
    try:
        return list_interview_blueprints(
            resume_id,
            db,
            offset=offset,
            limit=limit,
            job_id=job_id,
        )
    except BlueprintResumeNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview blueprints could not be retrieved.",
        ) from error


@router.delete(
    "/interview-preparation/blueprints/{blueprint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_interview_blueprint(
    blueprint_id: int,
    db: Session = Depends(get_db),
) -> None:
    try:
        delete_interview_blueprint(blueprint_id, db)
    except InterviewBlueprintNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            500,
            "The interview blueprint could not be deleted.",
        ) from error
