from sqlalchemy.orm import Session

from app.models.learning_roadmap import (
    JobLearningRoadmapResponse,
    LearningRoadmapItem,
)
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)
from app.services.match_explaination_service import explain_match


def build_learning_roadmap(
    resume_id: int,
    job_id: int,
    session: Session,
) -> JobLearningRoadmapResponse:
    """Build a deterministic roadmap from an existing match explanation."""
    explanation = explain_match(
        resume_id=resume_id,
        job_id=job_id,
        session=session,
    )

    roadmap = [
        LearningRoadmapItem(
            skill=skill,
            priority="high",
            reason="Required skill missing from the resume.",
        )
        for skill in explanation.missing_required_skills
    ]

    return JobLearningRoadmapResponse(
        resume_id=explanation.resume_id,
        job_id=explanation.job_id,
        total_missing_skills=len(roadmap),
        roadmap=roadmap,
    )