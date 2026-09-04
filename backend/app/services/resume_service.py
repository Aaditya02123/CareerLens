from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.models.resume import ResumeUploadResponse


STORAGE_DIRECTORY = (
    Path(__file__).resolve().parents[2] / "storage" / "resumes"
)

ALLOWED_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": (
        "application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document"
    ),
}


class UnsupportedResumeTypeError(ValueError):
    """Raised when an uploaded file is not a supported resume type."""


async def store_resume(upload_file: UploadFile) -> ResumeUploadResponse:
    """Validate and store a resume in local development storage."""
    original_filename = upload_file.filename
    content_type = upload_file.content_type

    if not original_filename:
        raise UnsupportedResumeTypeError("A filename is required.")

    file_extension = Path(original_filename).suffix.lower()
    expected_content_type = ALLOWED_CONTENT_TYPES.get(file_extension)

    if expected_content_type is None:
        raise UnsupportedResumeTypeError(
            "Only PDF and DOCX resume files are supported."
        )

    if content_type != expected_content_type:
        raise UnsupportedResumeTypeError(
            f"Expected content type {expected_content_type}."
        )

    STORAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}{file_extension}"
    destination = STORAGE_DIRECTORY / stored_filename

    try:
        with destination.open("wb") as output_file:
            while chunk := await upload_file.read(1024 * 1024):
                output_file.write(chunk)
    finally:
        await upload_file.close()

    return ResumeUploadResponse(
        original_filename=original_filename,
        content_type=content_type,
        stored_filename=stored_filename,
    )