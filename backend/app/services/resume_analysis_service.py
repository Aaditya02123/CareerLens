from sqlalchemy.orm import Session

from app.models.resume import ResumeAnalysisResponse
from app.repositories.resume_analysis_repository import (
    ResumeAnalysisRepository,
)
from app.repositories.resume_repository import ResumeRepository
from app.services.resume_parser import parse_resume_text
from app.services.resume_service import extract_resume_text
from app.services.skill_categorizer import categorize_skills
from app.services.skill_extractor import extract_skills


class ResumeRecordNotFoundError(LookupError):
    """Raised when no database record exists for a stored resume."""


def analyze_resume(
    stored_filename: str,
    session: Session,
) -> ResumeAnalysisResponse:
    """
    Extract and analyze a resume.

    The analysis is regenerated every time this service is called so that
    parser improvements are immediately reflected in the persisted result.

    This is intentional during the development phase. Later we can add
    parser-version tracking instead of reparsing every request.
    """
    resume_repository = ResumeRepository(session)

    resume = resume_repository.get_by_stored_filename(
        stored_filename
    )

    if resume is None:
        raise ResumeRecordNotFoundError(
            "No database record exists for the requested resume."
        )

    extracted_resume = extract_resume_text(
        stored_filename
    )

    structured_resume = parse_resume_text(
        extracted_resume.text
    )

    extracted_skills = extract_skills(
        extracted_resume.text
    )

    categorized_skills = categorize_skills(
        extracted_skills.skills
    )

    analysis_repository = ResumeAnalysisRepository(session)

    existing_analysis = analysis_repository.get_by_resume_id(
        resume.id
    )

    structured_resume_data = structured_resume.model_dump()
    categorized_skills_data = categorized_skills.model_dump()

    if existing_analysis is None:
        analysis_repository.create(
            resume_id=resume.id,
            structured_resume=structured_resume_data,
            categorized_skills=categorized_skills_data,
        )
    else:
        analysis_repository.update(
            analysis=existing_analysis,
            structured_resume=structured_resume_data,
            categorized_skills=categorized_skills_data,
        )

    return ResumeAnalysisResponse(
        structured_resume=structured_resume,
        categorized_skills=categorized_skills,
    )