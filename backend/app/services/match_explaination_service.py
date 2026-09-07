from sqlalchemy.orm import Session

from app.models.match_explaination import MatchExplanationResponse
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
    """Build concise, deterministic explanations."""
    factors: list[str] = []
    has_required_skills = _has_required_skills(
        matched_required_skills=matched_required_skills,
        missing_required_skills=missing_required_skills,
    )

    if has_required_skills and required_skill_score == 1.0:
        factors.append("All required skills are matched.")

    if (
        has_required_skills
        and required_skill_score < 1.0
        and missing_required_skills
    ):
        factors.append("Some required skills are missing.")

    if matched_preferred_skills:
        factors.append("Some preferred skills are also matched.")

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


def explain_match(
    resume_id: int,
    job_id: int,
    session: Session,
) -> MatchExplanationResponse:
    """Explain an existing hybrid match result."""
    hybrid_match = calculate_hybrid_match(
        resume_id=resume_id,
        job_id=job_id,
        session=session,
    )

    factors = _primary_factors(
        required_skill_score=hybrid_match.required_skill_score,
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
        match_level=_match_level(hybrid_match.hybrid_score),
        skill_gap_count=len(
            hybrid_match.missing_required_skills
        ),
        primary_factors=factors,
    )