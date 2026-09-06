import math

from sqlalchemy.orm import Session

from app.models.jobs import Job
from app.models.resume import StructuredResume
from app.models.resume_analysis import ResumeAnalysis
from app.models.semantic_matching import SemanticMatchResult
from app.models.skills import CategorizedSkillResult
from app.repositories.job_repository import JobRepository
from app.repositories.resume_analysis_repository import (
    ResumeAnalysisRepository,
)
from app.services.embedding_service import embed_text


class ResumeAnalysisNotFoundError(LookupError):
    """Raised when no persisted analysis exists for a resume."""


class JobNotFoundError(LookupError):
    """Raised when a requested job does not exist."""


def _unique_values(values: list[str]) -> list[str]:
    """Remove duplicate values while preserving readable order."""
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned_value = value.strip()
        comparison_value = cleaned_value.casefold()

        if not cleaned_value or comparison_value in seen:
            continue

        seen.add(comparison_value)
        result.append(cleaned_value)

    return result


def _resume_text(analysis: ResumeAnalysis) -> str:
    """Build deterministic labeled text from persisted resume analysis."""
    structured_resume = StructuredResume.model_validate(
        analysis.structured_resume
    )
    categorized_skills = CategorizedSkillResult.model_validate(
        analysis.categorized_skills
    )

    categorized_skill_names = [
        skill.name
        for skill in categorized_skills.skills
    ]

    skills = _unique_values(
        [
            *structured_resume.skills,
            *categorized_skill_names,
        ]
    )

    sections: list[str] = []

    if skills:
        sections.extend(["Skills:", *skills])

    if structured_resume.education:
        sections.extend(["Education:", *structured_resume.education])

    if structured_resume.experience:
        sections.extend(["Experience:", *structured_resume.experience])

    if structured_resume.projects:
        sections.extend(["Projects:", *structured_resume.projects])

    if structured_resume.certifications:
        sections.extend(
            ["Certifications:", *structured_resume.certifications]
        )

    return "\n".join(sections)


def _job_text(job: Job) -> str:
    """Build deterministic role-focused text from a job record."""
    sections: list[str] = [
        "Title:",
        job.title,
        "Description:",
        job.description,
    ]

    if job.responsibilities:
        sections.extend(
            ["Responsibilities:", *job.responsibilities]
        )

    if job.required_skills:
        sections.extend(
            ["Required Skills:", *job.required_skills]
        )

    if job.preferred_skills:
        sections.extend(
            ["Preferred Skills:", *job.preferred_skills]
        )

    if job.experience_level:
        sections.extend(
            ["Experience Level:", job.experience_level]
        )

    return "\n".join(sections)


def _cosine_similarity(
    first_vector: list[float],
    second_vector: list[float],
) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(first_vector) != len(second_vector):
        raise ValueError("Embedding vectors must have the same length.")

    first_norm = math.sqrt(
        sum(value * value for value in first_vector)
    )
    second_norm = math.sqrt(
        sum(value * value for value in second_vector)
    )

    if first_norm == 0.0 or second_norm == 0.0:
        return 0.0

    dot_product = sum(
        first_value * second_value
        for first_value, second_value in zip(
            first_vector,
            second_vector,
        )
    )

    return dot_product / (first_norm * second_norm)


def calculate_semantic_match(
    resume_id: int,
    job_id: int,
    session: Session,
) -> SemanticMatchResult:
    """Calculate semantic similarity using persisted resume analysis."""
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

    resume_embedding = embed_text(_resume_text(analysis))
    job_embedding = embed_text(_job_text(job))

    cosine_similarity = _cosine_similarity(
        resume_embedding,
        job_embedding,
    )

    cosine_similarity = max(
        -1.0,
        min(1.0, cosine_similarity),
    )

    semantic_score = (cosine_similarity + 1.0) / 2.0

    return SemanticMatchResult(
        resume_id=resume_id,
        job_id=job_id,
        cosine_similarity=cosine_similarity,
        semantic_score=semantic_score,
    )