from app.models.resume import ResumeAnalysisResponse
from app.services.resume_parser import parse_resume_text
from app.services.resume_service import extract_resume_text
from app.services.skill_categorizer import categorize_skills
from app.services.skill_extractor import extract_skills


def analyze_resume(stored_filename: str) -> ResumeAnalysisResponse:
    """Build a consolidated analysis for an already-stored resume."""
    extracted_resume = extract_resume_text(stored_filename)

    structured_resume = parse_resume_text(extracted_resume.text)
    extracted_skills = extract_skills(extracted_resume.text)
    categorized_skills = categorize_skills(extracted_skills.skills)

    return ResumeAnalysisResponse(
        structured_resume=structured_resume,
        categorized_skills=categorized_skills,
    )