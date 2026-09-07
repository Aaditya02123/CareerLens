from dataclasses import dataclass
import math

from sqlalchemy.orm import Session

from app.models.hybrid_matching import HybridMatchResult
from app.repositories.job_repository import JobRepository
from app.services.matching_service import (
    JobNotFoundError as DeterministicJobNotFoundError,
    ResumeAnalysisNotFoundError as DeterministicResumeAnalysisNotFoundError,
    calculate_match,
)
from app.services.semantic_matching_service import (
    JobNotFoundError as SemanticJobNotFoundError,
    ResumeAnalysisNotFoundError as SemanticResumeAnalysisNotFoundError,
    calculate_semantic_match,
)


@dataclass(frozen=True)
class HybridMatchingConfig:
    """Configurable weights for hybrid matching."""

    required_skill_weight: float = 0.60
    semantic_weight: float = 0.40

    def __post_init__(self) -> None:
        if self.required_skill_weight < 0.0:
            raise ValueError(
                "required_skill_weight cannot be negative."
            )

        if self.semantic_weight < 0.0:
            raise ValueError(
                "semantic_weight cannot be negative."
            )

        if not math.isclose(
            self.required_skill_weight + self.semantic_weight,
            1.0,
            abs_tol=1e-9,
        ):
            raise ValueError(
                "Hybrid matching weights must sum to 1.0 "
                "within floating-point tolerance."
            )


class ResumeAnalysisNotFoundError(LookupError):
    """Raised when no persisted analysis exists for a resume."""


class JobNotFoundError(LookupError):
    """Raised when a requested job does not exist."""


def calculate_hybrid_match(
    resume_id: int,
    job_id: int,
    session: Session,
    config: HybridMatchingConfig | None = None,
) -> HybridMatchResult:
    """Combine deterministic and semantic matching results."""
    matching_config = config or HybridMatchingConfig()

    job_repository = JobRepository(session)
    job = job_repository.get_by_id(job_id)

    if job is None:
        raise JobNotFoundError("The requested job was not found.")

    try:
        deterministic_match = calculate_match(
            resume_id=resume_id,
            job_id=job_id,
            session=session,
        )
    except DeterministicResumeAnalysisNotFoundError as error:
        raise ResumeAnalysisNotFoundError(str(error)) from error
    except DeterministicJobNotFoundError as error:
        raise JobNotFoundError(str(error)) from error

    try:
        semantic_match = calculate_semantic_match(
            resume_id=resume_id,
            job_id=job_id,
            session=session,
        )
    except SemanticResumeAnalysisNotFoundError as error:
        raise ResumeAnalysisNotFoundError(str(error)) from error
    except SemanticJobNotFoundError as error:
        raise JobNotFoundError(str(error)) from error

    if job.required_skills:
        hybrid_score = (
            matching_config.required_skill_weight
            * deterministic_match.required_skill_score
            + matching_config.semantic_weight
            * semantic_match.semantic_score
        )
    else:
        hybrid_score = semantic_match.semantic_score

    return HybridMatchResult(
        resume_id=resume_id,
        job_id=job_id,
        required_skill_score=(
            deterministic_match.required_skill_score
        ),
        semantic_score=semantic_match.semantic_score,
        preferred_skill_score=(
            deterministic_match.preferred_skill_score
        ),
        hybrid_score=hybrid_score,
        required_skill_weight=(
            matching_config.required_skill_weight
        ),
        semantic_weight=matching_config.semantic_weight,
        matched_required_skills=(
            deterministic_match.matched_required_skills
        ),
        missing_required_skills=(
            deterministic_match.missing_required_skills
        ),
        matched_preferred_skills=(
            deterministic_match.matched_preferred_skills
        ),
    )