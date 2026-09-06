from sqlalchemy.orm import Session

from app.models.resume import (
    ResumeAnalysisResponse,
    StructuredResume,
)
from app.models.skills import CategorizedSkillResult
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
    """Return a persisted analysis or create it when one does not exist."""
    resume_repository = ResumeRepository(session)
    resume = resume_repository.get_by_stored_filename(stored_filename)

    if resume is None:
        raise ResumeRecordNotFoundError(
            "No database record exists for the requested resume."
        )

    analysis_repository = ResumeAnalysisRepository(session)
    existing_analysis = analysis_repository.get_by_resume_id(resume.id)

    if existing_analysis is not None:
        structured_resume = StructuredResume.model_validate(
            existing_analysis.structured_resume
        )
        categorized_skills = CategorizedSkillResult.model_validate(
            existing_analysis.categorized_skills
        )

        return ResumeAnalysisResponse(
            structured_resume=structured_resume,
            categorized_skills=categorized_skills,
        )

    extracted_resume = extract_resume_text(stored_filename)
    structured_resume = parse_resume_text(extracted_resume.text)
    extracted_skills = extract_skills(extracted_resume.text)
    categorized_skills = categorize_skills(extracted_skills.skills)

    analysis_repository.create(
        resume_id=resume.id,
        structured_resume=structured_resume.model_dump(),
        categorized_skills=categorized_skills.model_dump(),
    )

    return ResumeAnalysisResponse(
        structured_resume=structured_resume,
        categorized_skills=categorized_skills,
    )