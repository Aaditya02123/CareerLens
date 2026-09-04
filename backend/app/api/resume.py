from fastapi import APIRouter, File, HTTPException, UploadFile
from app.models.resume import ResumeUploadResponse
from app.services.resume_service import (UnsupportedResumeTypeError, store_resume,)

router = APIRouter()

@router.post("/resume", response_model=ResumeUploadResponse)
async def upload_resume(file : UploadFile = File(...),) -> ResumeUploadResponse:
    """Receive and store a resume file."""
    try:
        return await store_resume(file)
    except UnsupportedResumeTypeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(status_code=500, detail="The resume could not be stored.",) from error