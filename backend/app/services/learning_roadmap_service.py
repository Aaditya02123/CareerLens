from sqlalchemy.orm import Session

from app.models.learning_roadmap import (
    JobLearningRoadmapResponse,
    LearningRoadmapItem,
)
from app.services.skill_gap_service import get_skill_gap


def build_learning_roadmap(
    resume_id: int,
    job_id: int,
    session: Session,
) -> JobLearningRoadmapResponse:
    """Build a deterministic roadmap from the authoritative skill-gap analysis."""

    skill_gap = get_skill_gap(
        resume_id=resume_id,
        job_id=job_id,
        session=session,
    )

    roadmap: list[LearningRoadmapItem] = []

    for item in skill_gap.partial:
        roadmap.append(
            LearningRoadmapItem(
                skill=item.skill,
                status="partial",
                priority="medium",
                reason=(
                    "Required skill has partial supporting evidence "
                    "in the resume."
                ),
            )
        )

    for item in skill_gap.missing:
        roadmap.append(
            LearningRoadmapItem(
                skill=item.skill,
                status="missing",
                priority="high",
                reason="Required skill is missing from the resume.",
            )
        )

    return JobLearningRoadmapResponse(
        resume_id=skill_gap.resume_id,
        job_id=skill_gap.job_id,
        total_items=len(roadmap),
        roadmap=roadmap,
    )