from sqlalchemy.orm import Session

from app.models.learning_roadmap import (
    JobLearningRoadmapResponse,
    LearningRoadmapItem,
)
from app.repositories.learning_roadmap_repository import (
    LearningRoadmapRepository,
)
from app.services.skill_gap_service import get_skill_gap


def _response_from_persisted_roadmap(
    roadmap,
) -> JobLearningRoadmapResponse:
    """Convert persisted roadmap items to the existing API response."""
    response_items = [
        LearningRoadmapItem(
            skill=item.skill,
            status=item.skill_gap_status,
            priority=item.priority,
            reason=item.reason,
        )
        for item in roadmap.items
    ]

    return JobLearningRoadmapResponse(
        resume_id=roadmap.resume_id,
        job_id=roadmap.job_id,
        total_items=len(response_items),
        roadmap=response_items,
    )


def build_learning_roadmap(
    resume_id: int,
    job_id: int,
    session: Session,
) -> JobLearningRoadmapResponse:
    """
    Return an existing persisted roadmap or create one from skill-gap data.
    """
    roadmap_repository = LearningRoadmapRepository(session)

    persisted_roadmap = (
        roadmap_repository.get_by_resume_and_job(
            resume_id=resume_id,
            job_id=job_id,
        )
    )

    if persisted_roadmap is not None:
        return _response_from_persisted_roadmap(
            persisted_roadmap,
        )

    skill_gap = get_skill_gap(
        resume_id=resume_id,
        job_id=job_id,
        session=session,
    )

    roadmap_items: list[LearningRoadmapItem] = []

    for item in skill_gap.partial:
        roadmap_items.append(
            LearningRoadmapItem(
                skill=item.skill,
                status="partial",
                priority="medium",
                reason="Required skill has partial supporting evidence in the resume."
            )
        )

    for item in skill_gap.missing:
        roadmap_items.append(
            LearningRoadmapItem(
                skill=item.skill,
                status="missing",
                priority="high",
                reason="Required skill is missing from the resume.",
            )
        )

    persisted_roadmap = roadmap_repository.create(
        resume_id=skill_gap.resume_id,
        job_id=skill_gap.job_id,
    )

    for item in roadmap_items:
        roadmap_repository.add_item(
            roadmap=persisted_roadmap,
            skill=item.skill,
            skill_gap_status=item.status,
            priority=item.priority,
            reason=item.reason,
        )

    return JobLearningRoadmapResponse(
        resume_id=skill_gap.resume_id,
        job_id=skill_gap.job_id,
        total_items=len(roadmap_items),
        roadmap=roadmap_items,
    )