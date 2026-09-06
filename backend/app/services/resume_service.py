from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from fastapi import UploadFile
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.resume import (
    Resume,
    ResumeTextResponse,
    ResumeUploadResponse,
)
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository


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
    """Raised when an uploaded or stored file is unsupported."""


class ResumeNotFoundError(FileNotFoundError):
    """Raised when a stored resume cannot be found."""


class ResumeExtractionError(RuntimeError):
    """Raised when resume text cannot be extracted."""


class UserNotFoundError(LookupError):
    """Raised when a resume operation references a missing user."""


async def store_resume(
    upload_file: UploadFile,
    user_id: int,
    session: Session,
) -> ResumeUploadResponse:
    """Store a resume file and create its database record."""
    user_repository = UserRepository(session)

    if user_repository.get_by_id(user_id) is None:
        raise UserNotFoundError("The specified user was not found.")

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
    file_stored = False

    try:
        with destination.open("wb") as output_file:
            while chunk := await upload_file.read(1024 * 1024):
                output_file.write(chunk)

        file_stored = True
    finally:
        await upload_file.close()

    try:
        resume_repository = ResumeRepository(session)
        resume_repository.create(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
        )
    except SQLAlchemyError:
        if file_stored:
            try:
                destination.unlink()
            except OSError:
                pass

        raise

    return ResumeUploadResponse(
        original_filename=original_filename,
        content_type=content_type,
        stored_filename=stored_filename,
    )


def get_resumes_by_user_id(
    user_id: int,
    session: Session,
) -> list[Resume]:
    """Return all resumes belonging to an existing user."""
    user_repository = UserRepository(session)

    if user_repository.get_by_id(user_id) is None:
        raise UserNotFoundError("The specified user was not found.")

    resume_repository = ResumeRepository(session)
    return resume_repository.get_by_user_id(user_id)


def _get_stored_resume_path(stored_filename: str) -> Path:
    """Resolve a stored filename safely inside the resume storage directory."""
    if not stored_filename:
        raise ResumeNotFoundError("A stored filename is required.")

    if Path(stored_filename).name != stored_filename:
        raise UnsupportedResumeTypeError("Invalid stored filename.")

    file_extension = Path(stored_filename).suffix.lower()

    if file_extension not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedResumeTypeError(
            "Only stored PDF and DOCX resumes are supported."
        )

    storage_directory = STORAGE_DIRECTORY.resolve()
    resume_path = (storage_directory / stored_filename).resolve()

    try:
        resume_path.relative_to(storage_directory)
    except ValueError as error:
        raise UnsupportedResumeTypeError(
            "Invalid stored filename."
        ) from error

    if not resume_path.is_file():
        raise ResumeNotFoundError("The requested resume was not found.")

    return resume_path


def _extract_pdf_text(resume_path: Path) -> str:
    reader = PdfReader(resume_path)
    return "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    ).strip()


def _extract_docx_text(resume_path: Path) -> str:
    document = Document(resume_path)
    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    ).strip()


def extract_resume_text(stored_filename: str) -> ResumeTextResponse:
    """Extract raw text from an already-stored PDF or DOCX resume."""
    resume_path = _get_stored_resume_path(stored_filename)

    try:
        if resume_path.suffix.lower() == ".pdf":
            text = _extract_pdf_text(resume_path)
        else:
            text = _extract_docx_text(resume_path)
    except (
        PdfReadError,
        BadZipFile,
        PackageNotFoundError,
        OSError,
    ) as error:
        raise ResumeExtractionError(
            "The resume text could not be extracted."
        ) from error

    return ResumeTextResponse(
        stored_filename=stored_filename,
        text=text,
    )