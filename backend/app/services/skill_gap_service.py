from sqlalchemy.orm import Session

from app.models.match_explaination import MatchEvidence
from app.models.skill_gap import (
    SkillGapItem,
    SkillGapResponse,
)
from app.services.match_explaination_service import explain_match


def _evidence_by_skill(
    evidence: list[MatchEvidence],
) -> dict[str, list[MatchEvidence]]:
    """Group existing evidence by case-insensitive skill name."""
    grouped: dict[str, list[MatchEvidence]] = {}

    for item in evidence:
        key = item.skill.casefold().strip()

        if not key:
            continue

        grouped.setdefault(key, []).append(item)

    return grouped


def get_skill_gap(
    resume_id: int,
    job_id: int,
    session: Session,
) -> SkillGapResponse:
    """
    Build a skill-gap response from the authoritative match explanation.

    Partial classification is intentionally empty because the current
    matching system does not provide reliable related-skill relationships.
    """
    explanation = explain_match(
        resume_id=resume_id,
        job_id=job_id,
        session=session,
    )

    evidence_by_skill = _evidence_by_skill(
        explanation.evidence,
    )

    matched: list[SkillGapItem] = []

    for skill in explanation.matched_required_skills:
        matched.append(
            SkillGapItem(
                skill=skill,
                status="matched",
                evidence=evidence_by_skill.get(
                    skill.casefold().strip(),
                    [],
                ),
                reason=(
                    "Required skill is directly matched "
                    "by the resume."
                ),
                priority="low",
            )
        )

    missing: list[SkillGapItem] = []

    for skill in explanation.missing_required_skills:
        missing.append(
            SkillGapItem(
                skill=skill,
                status="missing",
                evidence=[],
                reason=(
                    "No matching or supporting resume "
                    "evidence was found."
                ),
                priority="high",
            )
        )

    partial: list[SkillGapItem] = []

    return SkillGapResponse(
        resume_id=explanation.resume_id,
        job_id=explanation.job_id,
        total_required_skills=(
            len(matched)
            + len(partial)
            + len(missing)
        ),
        matched_count=len(matched),
        partial_count=len(partial),
        missing_count=len(missing),
        matched=matched,
        partial=partial,
        missing=missing,
    )