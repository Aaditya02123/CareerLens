from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.resume import (
    ResumeTextResponse,
    ResumeUploadResponse,
    StructuredResume,
)
from app.models.skills import SkillExtractionResult
from app.services.resume_parser import parse_resume_text
from app.services.resume_service import (
    ResumeExtractionError,
    ResumeNotFoundError,
    UnsupportedResumeTypeError,
    extract_resume_text,
    store_resume,
)
from app.services.skill_extractor import extract_skills

router = APIRouter()


@router.post("/resume", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
) -> ResumeUploadResponse:
    """Receive and store a resume file."""
    try:
        return await store_resume(file)
    except UnsupportedResumeTypeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail="The resume could not be stored.",
        ) from error


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