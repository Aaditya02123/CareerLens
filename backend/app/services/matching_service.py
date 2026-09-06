from sqlalchemy.orm import Session

from app.models.jobs import Job
from app.models.matching import MatchResult
from app.models.resume_analysis import ResumeAnalysis
from app.models.skills import CategorizedSkillResult
from app.repositories.job_repository import JobRepository
from app.repositories.resume_analysis_repository import (
    ResumeAnalysisRepository,
)


class ResumeAnalysisNotFoundError(LookupError):
    """Raised when no persisted analysis exists for a resume."""


class JobNotFoundError(LookupError):
    """Raised when a requested job does not exist."""


def _normalized_skill(value: str) -> str:
    """Return a case-insensitive comparison value for a skill."""
    return value.strip().casefold()


def _unique_skills(skills: list[str]) -> list[str]:
    """Remove duplicate skills while preserving readable values and order."""
    unique_values: list[str] = []
    seen: set[str] = set()

    for skill in skills:
        normalized = _normalized_skill(skill)

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        unique_values.append(skill.strip())

    return unique_values


def _resume_skill_names(analysis: ResumeAnalysis) -> list[str]:
    """Validate and extract names from persisted categorized skills."""
    categorized_skills = CategorizedSkillResult.model_validate(
        analysis.categorized_skills
    )

    return _unique_skills(
        [skill.name for skill in categorized_skills.skills]
    )


def _match_skills(
    resume_skills: list[str],
    job_skills: list[str],
) -> tuple[list[str], list[str], float]:
    """Compare skills using exact, case-insensitive matching."""
    unique_job_skills = _unique_skills(job_skills)
    resume_skill_keys = {
        _normalized_skill(skill)
        for skill in resume_skills
    }

    matched_skills = [
        skill
        for skill in unique_job_skills
        if _normalized_skill(skill) in resume_skill_keys
    ]

    missing_skills = [
        skill
        for skill in unique_job_skills
        if _normalized_skill(skill) not in resume_skill_keys
    ]

    if not unique_job_skills:
        score = 0.0
    else:
        score = len(matched_skills) / len(unique_job_skills)

    return matched_skills, missing_skills, score


def calculate_match(
    resume_id: int,
    job_id: int,
    session: Session,
) -> MatchResult:
    """Calculate a deterministic skill match for a resume and job."""
    analysis_repository = ResumeAnalysisRepository(session)
    analysis = analysis_repository.get_by_resume_id(resume_id)

    if analysis is None:
        raise ResumeAnalysisNotFoundError(
            "No persisted resume analysis was found."
        )

    job_repository = JobRepository(session)
    job = job_repository.get_by_id(job_id)

    if job is None:
        raise JobNotFoundError("The requested job was not found.")

    resume_skills = _resume_skill_names(analysis)

    matched_required, missing_required, required_score = _match_skills(
        resume_skills=resume_skills,
        job_skills=job.required_skills,
    )

    matched_preferred, _, preferred_score = _match_skills(
        resume_skills=resume_skills,
        job_skills=job.preferred_skills,
    )

    return MatchResult(
        job_id=job.id,
        resume_id=resume_id,
        required_skill_score=required_score,
        preferred_skill_score=preferred_score,
        matched_required_skills=matched_required,
        missing_required_skills=missing_required,
        matched_preferred_skills=matched_preferred,
    )