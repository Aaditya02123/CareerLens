from app.data.learning_effort_catalog import (
    get_learning_effort_estimate,
)
from app.data.learning_resource_catalog import normalize_skill_key
from app.models.learning_effort import (
    LearningEffortGapStatus,
    LearningEffortResponse,
)


def estimate_learning_effort(
    skill: str,
    gap_status: LearningEffortGapStatus,
) -> LearningEffortResponse:
    """Return a deterministic effort range for a roadmap skill."""
    if not isinstance(skill, str):
        raise TypeError("skill must be a string.")

    if not isinstance(gap_status, str) or gap_status not in {"partial","missing",}:
        raise ValueError(
            "gap_status must be either 'partial' or 'missing'."
        )

    normalized_skill = normalize_skill_key(skill)

    if not normalized_skill:
        raise ValueError("skill must not be empty.")

    estimate = get_learning_effort_estimate(normalized_skill)

    if estimate is None:
        return LearningEffortResponse(
            skill=normalized_skill,
            gap_status=gap_status,
            minimum_hours=None,
            maximum_hours=None,
            available=False,
        )

    if gap_status == "partial":
        minimum_hours = estimate.partial_min_hours
        maximum_hours = estimate.partial_max_hours
    else:
        minimum_hours = estimate.missing_min_hours
        maximum_hours = estimate.missing_max_hours

    return LearningEffortResponse(
        skill=normalized_skill,
        gap_status=gap_status,
        minimum_hours=minimum_hours,
        maximum_hours=maximum_hours,
        available=True,
    )