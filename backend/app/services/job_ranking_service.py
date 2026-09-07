from sqlalchemy.orm import Session

from app.models.hybrid_matching import HybridMatchResult
from app.models.job_ranking import (
    JobRankingResponse,
    RankedJobMatch,
)
from app.repositories.job_repository import JobRepository
from app.repositories.resume_analysis_repository import (
    ResumeAnalysisRepository,
)
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
    calculate_hybrid_match,
)


JOB_BATCH_SIZE = 100


def _get_all_jobs(session: Session):
    """Retrieve all jobs in batches using the existing repository method."""
    repository = JobRepository(session)
    jobs = []
    offset = 0

    while True:
        batch = repository.list_jobs(
            limit=JOB_BATCH_SIZE,
            offset=offset,
        )

        if not batch:
            break

        jobs.extend(batch)
        offset += len(batch)

        if len(batch) < JOB_BATCH_SIZE:
            break

    return jobs


def rank_jobs_for_resume(
    resume_id: int,
    session: Session,
    limit: int = 10,
) -> JobRankingResponse:
    """Calculate and rank hybrid matches for all available jobs."""
    if limit <= 0:
        raise ValueError("Limit must be greater than zero.")

    analysis_repository = ResumeAnalysisRepository(session)

    if analysis_repository.get_by_resume_id(resume_id) is None:
        raise ResumeAnalysisNotFoundError(
            "No persisted resume analysis was found."
        )

    jobs = _get_all_jobs(session)
    hybrid_matches: list[HybridMatchResult] = []

    for job in jobs:
        hybrid_matches.append(
            calculate_hybrid_match(
                resume_id=resume_id,
                job_id=job.id,
                session=session,
            )
        )

    hybrid_matches.sort(
        key=lambda match: (
            -match.hybrid_score,
            match.job_id,
        )
    )

    ranked_matches = [
        RankedJobMatch(
            rank=rank,
            job_id=match.job_id,
            resume_id=match.resume_id,
            hybrid_score=match.hybrid_score,
            required_skill_score=match.required_skill_score,
            semantic_score=match.semantic_score,
            preferred_skill_score=match.preferred_skill_score,
            matched_required_skills=match.matched_required_skills,
            missing_required_skills=match.missing_required_skills,
            matched_preferred_skills=match.matched_preferred_skills,
        )
        for rank, match in enumerate(
            hybrid_matches[:limit],
            start=1,
        )
    ]

    return JobRankingResponse(
        resume_id=resume_id,
        matches=ranked_matches,
    )