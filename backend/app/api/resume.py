from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.resume import (
    ResumeAnalysisResponse,
    ResumeResponse,
    ResumeTextResponse,
    ResumeUploadResponse,
    StructuredResume,
)
from app.models.skills import SkillExtractionResult
from app.services.resume_analysis_service import analyze_resume
from app.services.resume_parser import parse_resume_text
from app.services.resume_service import (
    ResumeExtractionError,
    ResumeNotFoundError,
    UnsupportedResumeTypeError,
    UserNotFoundError,
    extract_resume_text,
    get_resumes_by_user_id,
    store_resume,
)
from app.services.skill_extractor import extract_skills

router = APIRouter()


@router.post("/resume", response_model=ResumeUploadResponse)
async def upload_resume(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ResumeUploadResponse:
    """Receive, store, and register a resume for a user."""
    try:
        return await store_resume(
            upload_file=file,
            user_id=user_id,
            session=db,
        )
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="The specified user was not found.",
        ) from error
    except UnsupportedResumeTypeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="The resume could not be registered.",
        ) from error
    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail="The resume could not be stored.",
        ) from error


@router.get(
    "/users/{user_id}/resumes",
    response_model=list[ResumeResponse],
)
def get_user_resumes(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[ResumeResponse]:
    """Return all resumes belonging to a user."""
    try:
        resumes = get_resumes_by_user_id(
            user_id=user_id,
            session=db,
        )
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="The specified user was not found.",
        ) from error

    return [
        ResumeResponse.model_validate(resume)
        for resume in resumes
    ]


@router.get(
    "/resume/{stored_filename}/text",
    response_model=ResumeTextResponse,
)
def read_resume_text(stored_filename: str) -> ResumeTextResponse:
    """Extract raw text from an already-stored resume."""
    try:
        return extract_resume_text(stored_filename)
    except ResumeNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except UnsupportedResumeTypeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ResumeExtractionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get(
    "/resume/{stored_filename}/parsed",
    response_model=StructuredResume,
)
def read_parsed_resume(stored_filename: str) -> StructuredResume:
    """Parse an already-stored resume into structured fields."""
    try:
        extracted_resume = extract_resume_text(stored_filename)
        return parse_resume_text(extracted_resume.text)
    except ResumeNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except UnsupportedResumeTypeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ResumeExtractionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get(
    "/resume/{stored_filename}/skills",
    response_model=SkillExtractionResult,
)
def read_resume_skills(stored_filename: str) -> SkillExtractionResult:
    """Extract canonical skills from an already-stored resume."""
    try:
        extracted_resume = extract_resume_text(stored_filename)
        return extract_skills(extracted_resume.text)
    except ResumeNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except UnsupportedResumeTypeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ResumeExtractionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get(
    "/resume/{stored_filename}/analysis",
    response_model=ResumeAnalysisResponse,
)
def read_resume_analysis(stored_filename: str) -> ResumeAnalysisResponse:
    """Return the consolidated analysis for an already-stored resume."""
    try:
        return analyze_resume(stored_filename)
    except ResumeNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except UnsupportedResumeTypeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ResumeExtractionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error