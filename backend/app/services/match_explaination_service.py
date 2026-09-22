import re

from sqlalchemy.orm import Session

from app.models.jobs import Job
from app.models.match_explaination import (
    MatchEvidence,
    MatchExplanationResponse,
)
from app.models.resume import StructuredResume
from app.repositories.job_repository import JobRepository
from app.repositories.resume_analysis_repository import (
    ResumeAnalysisRepository,
)
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
    calculate_hybrid_match,
)


def _match_level(hybrid_score: float) -> str:
    """Convert a hybrid score into a deterministic match level."""
    if hybrid_score >= 0.75:
        return "strong"

    if hybrid_score >= 0.50:
        return "partial"

    return "weak"


def _has_required_skills(
    matched_required_skills: list[str],
    missing_required_skills: list[str],
) -> bool:
    """Determine whether the job contains required-skill data."""
    return bool(
        matched_required_skills
        or missing_required_skills
    )


def _primary_factors(
    required_skill_score: float,
    matched_required_skills: list[str],
    missing_required_skills: list[str],
    matched_preferred_skills: list[str],
    semantic_score: float,
) -> list[str]:
    """Build concise deterministic explanations."""
    factors: list[str] = []

    has_required_skills = _has_required_skills(
        matched_required_skills=matched_required_skills,
        missing_required_skills=missing_required_skills,
    )

    if has_required_skills and required_skill_score == 1.0:
        factors.append(
            "All required skills are matched."
        )

    if (
        has_required_skills
        and required_skill_score < 1.0
        and missing_required_skills
    ):
        factors.append(
            "Some required skills are missing."
        )

    if matched_preferred_skills:
        factors.append(
            "Some preferred skills are also matched."
        )

    if semantic_score >= 0.70:
        factors.append(
            "Resume and job descriptions have strong semantic similarity."
        )
    elif semantic_score >= 0.50:
        factors.append(
            "Resume and job descriptions have moderate semantic similarity."
        )
    else:
        factors.append(
            "Resume and job descriptions have low semantic similarity."
        )

    return factors


def _normalize_for_matching(value: str) -> str:
    """Normalize text for conservative skill-evidence matching."""
    return re.sub(
        r"\s+",
        " ",
        value.casefold().strip(),
    )


def _skill_occurs_in_text(
    skill: str,
    text: str,
) -> bool:
    """Return whether a skill appears as a meaningful text match."""
    normalized_skill = _normalize_for_matching(skill)
    normalized_text = _normalize_for_matching(text)

    if not normalized_skill or not normalized_text:
        return False

    escaped_skill = re.escape(normalized_skill)

    return bool(
        re.search(
            rf"(?<!\w){escaped_skill}(?!\w)",
            normalized_text,
        )
    )


def _clean_text(value: str) -> str:
    """Normalize whitespace without changing the source meaning."""
    return re.sub(
        r"\s+",
        " ",
        value.strip(),
    )


def _source_title(value: str, fallback: str) -> str:
    """Extract a readable title from a structured resume entry."""
    lines = [
        _clean_text(line)
        for line in value.splitlines()
        if _clean_text(line)
    ]

    if lines:
        return lines[0][:160]

    return fallback


def _evidence_excerpt(
    value: str,
    skill: str,
) -> str:
    """Return the smallest useful source excerpt containing the skill."""
    lines = [
        _clean_text(line)
        for line in value.splitlines()
        if _clean_text(line)
    ]

    for line in lines:
        if _skill_occurs_in_text(skill, line):
            return line[:320]

    cleaned = _clean_text(value)

    return cleaned[:320]


def _resume_evidence_sections(
    structured_resume: StructuredResume,
) -> list[tuple[str, str, str]]:
    """
    Build searchable resume evidence sections.

    Returns:
        (source_type, source_title, source_text)
    """
    sections: list[tuple[str, str, str]] = []

    if structured_resume.skills:
        for skill in structured_resume.skills:
            cleaned_skill = _clean_text(skill)

            if cleaned_skill:
                sections.append(
                    (
                        "skill",
                        "Technical skills",
                        cleaned_skill,
                    )
                )

    for project in structured_resume.projects:
        cleaned_project = _clean_text(project)

        if cleaned_project:
            sections.append(
                (
                    "project",
                    _source_title(
                        project,
                        "Resume project",
                    ),
                    project,
                )
            )

    for experience in structured_resume.experience:
        cleaned_experience = _clean_text(experience)

        if cleaned_experience:
            sections.append(
                (
                    "experience",
                    _source_title(
                        experience,
                        "Work experience",
                    ),
                    experience,
                )
            )

    for education in structured_resume.education:
        cleaned_education = _clean_text(education)

        if cleaned_education:
            sections.append(
                (
                    "education",
                    _source_title(
                        education,
                        "Education",
                    ),
                    education,
                )
            )

    for certification in structured_resume.certifications:
        cleaned_certification = _clean_text(certification)

        if cleaned_certification:
            sections.append(
                (
                    "certification",
                    _source_title(
                        certification,
                        "Certification",
                    ),
                    certification,
                )
            )

    return sections


def _build_skill_evidence(
    structured_resume: StructuredResume,
    skills: list[str],
) -> list[MatchEvidence]:
    """Find concrete resume evidence for matched job skills."""
    evidence: list[MatchEvidence] = []
    sections = _resume_evidence_sections(structured_resume)

    seen: set[tuple[str, str, str]] = set()

    for skill in skills:
        for source_type, source_title, source_text in sections:
            if not _skill_occurs_in_text(
                skill,
                source_text,
            ):
                continue

            key = (
                skill.casefold(),
                source_type,
                source_title.casefold(),
            )

            if key in seen:
                continue

            seen.add(key)

            strength = (
                "direct"
                if source_type == "skill"
                else "supporting"
            )

            evidence.append(
                MatchEvidence(
                    skill=skill,
                    source_type=source_type,
                    source_title=source_title,
                    excerpt=_evidence_excerpt(
                        source_text,
                        skill,
                    ),
                    strength=strength,
                )
            )

    return evidence


def _all_matched_skills(
    matched_required_skills: list[str],
    matched_preferred_skills: list[str],
) -> list[str]:
    """Combine matched skills while preserving readable order."""
    result: list[str] = []
    seen: set[str] = set()

    for skill in [
        *matched_required_skills,
        *matched_preferred_skills,
    ]:
        normalized = skill.casefold().strip()

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        result.append(skill)

    return result


def explain_match(
    resume_id: int,
    job_id: int,
    session: Session,
) -> MatchExplanationResponse:
    """Explain an existing hybrid match with resume evidence."""
    hybrid_match = calculate_hybrid_match(
        resume_id=resume_id,
        job_id=job_id,
        session=session,
    )

    analysis_repository = ResumeAnalysisRepository(session)
    analysis = analysis_repository.get_by_resume_id(resume_id)

    if analysis is None:
        raise ResumeAnalysisNotFoundError(
            "No persisted resume analysis was found."
        )

    job_repository = JobRepository(session)
    job = job_repository.get_by_id(job_id)

    if job is None:
        raise JobNotFoundError(
            "The requested job was not found."
        )

    structured_resume = StructuredResume.model_validate(
        analysis.structured_resume
    )

    matched_skills = _all_matched_skills(
        matched_required_skills=(
            hybrid_match.matched_required_skills
        ),
        matched_preferred_skills=(
            hybrid_match.matched_preferred_skills
        ),
    )

    evidence = _build_skill_evidence(
        structured_resume=structured_resume,
        skills=matched_skills,
    )

    factors = _primary_factors(
        required_skill_score=(
            hybrid_match.required_skill_score
        ),
        matched_required_skills=(
            hybrid_match.matched_required_skills
        ),
        missing_required_skills=(
            hybrid_match.missing_required_skills
        ),
        matched_preferred_skills=(
            hybrid_match.matched_preferred_skills
        ),
        semantic_score=hybrid_match.semantic_score,
    )

    return MatchExplanationResponse(
        resume_id=hybrid_match.resume_id,
        job_id=hybrid_match.job_id,
        hybrid_score=hybrid_match.hybrid_score,
        required_skill_score=(
            hybrid_match.required_skill_score
        ),
        preferred_skill_score=(
            hybrid_match.preferred_skill_score
        ),
        semantic_score=hybrid_match.semantic_score,
        matched_required_skills=(
            hybrid_match.matched_required_skills
        ),
        missing_required_skills=(
            hybrid_match.missing_required_skills
        ),
        matched_preferred_skills=(
            hybrid_match.matched_preferred_skills
        ),
        match_level=_match_level(
            hybrid_match.hybrid_score
        ),
        skill_gap_count=len(
            hybrid_match.missing_required_skills
        ),
        primary_factors=factors,
        evidence=evidence,
    )