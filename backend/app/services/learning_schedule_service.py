from __future__ import annotations

import math
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.learning_preferences import (
    LearningPreferencesResponse,
)
from app.models.learning_roadmap import (
    LearningRoadmapProgressStatus,
)
from app.models.learning_schedule import (
    LearningScheduleItem,
    LearningScheduleResponse,
    LearningScheduleStatus,
)
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)
from app.services.learning_preferences_service import (
    LearningPreferencesUserNotFoundError,
    get_learning_preferences,
)
from app.services.learning_effort_service import (
    estimate_learning_effort,
)
from app.services.learning_roadmap_service import (
    build_learning_roadmap,
)


class ResumeNotFoundError(LookupError):
    """Raised when a schedule references a missing resume."""


class LearningRoadmapNotFoundError(LookupError):
    """Raised when no roadmap can be loaded for a resume/job pair."""


_VALID_PROGRESS_STATUSES = {
    "not_started",
    "in_progress",
    "completed",
}


def _safe_progress_status(value: object) -> LearningRoadmapProgressStatus:
    """Treat unknown persisted progress as not started for projection."""
    if value in _VALID_PROGRESS_STATUSES:
        return value  # type: ignore[return-value]

    return "not_started"


def _schedule_status(
    *,
    configured: bool,
    has_items: bool,
    all_items_completed: bool,
    remaining_available_items: int,
    remaining_items: int,
    target_completion_date: date | None,
    estimated_maximum_weeks: int,
) -> LearningScheduleStatus:
    """Apply schedule-status precedence in one deterministic place."""
    if not configured:
        return "not_configured"

    if not has_items or all_items_completed:
        return "completed"

    if remaining_available_items == 0:
        if remaining_items > 0:
            return "no_estimate"
        return "completed"

    if target_completion_date is None:
        return "no_target_date"

    projected_date = date.today() + timedelta(
        weeks=estimated_maximum_weeks,
    )

    if projected_date <= target_completion_date:
        return "on_track"

    return "at_risk"


def _build_response(
    *,
    roadmap,
    preferences: LearningPreferencesResponse,
) -> LearningScheduleResponse:
    response_items: list[LearningScheduleItem] = []
    remaining_minimum_hours = 0
    remaining_maximum_hours = 0
    remaining_available_items = 0
    remaining_items = 0
    all_items_completed = True

    for roadmap_item in roadmap.roadmap:
        progress_status = _safe_progress_status(
            roadmap_item.progress_status,
        )
        effort = estimate_learning_effort(
            skill=roadmap_item.skill,
            gap_status=roadmap_item.status,
        )

        response_items.append(
            LearningScheduleItem(
                roadmap_item_id=roadmap_item.id,
                skill=roadmap_item.skill,
                progress_status=progress_status,
                minimum_hours=effort.minimum_hours,
                maximum_hours=effort.maximum_hours,
                effort_available=effort.available,
            )
        )

        if progress_status != "completed":
            all_items_completed = False
            remaining_items += 1

            if effort.available:
                remaining_available_items += 1
                remaining_minimum_hours += effort.minimum_hours or 0
                remaining_maximum_hours += effort.maximum_hours or 0

    estimated_minimum_weeks = (
        math.ceil(remaining_minimum_hours / preferences.weekly_hours)
        if remaining_minimum_hours
        else 0
    )
    estimated_maximum_weeks = (
        math.ceil(remaining_maximum_hours / preferences.weekly_hours)
        if remaining_maximum_hours
        else 0
    )

    schedule_status = _schedule_status(
        configured=preferences.is_saved,
        has_items=bool(response_items),
        all_items_completed=all_items_completed,
        remaining_available_items=remaining_available_items,
        remaining_items=remaining_items,
        target_completion_date=preferences.target_completion_date,
        estimated_maximum_weeks=estimated_maximum_weeks,
    )

    return LearningScheduleResponse(
        resume_id=roadmap.resume_id,
        job_id=roadmap.job_id,
        configured=preferences.is_saved,
        weekly_hours=preferences.weekly_hours,
        target_completion_date=preferences.target_completion_date,
        pace=preferences.pace,
        remaining_minimum_hours=remaining_minimum_hours,
        remaining_maximum_hours=remaining_maximum_hours,
        estimated_minimum_weeks=estimated_minimum_weeks,
        estimated_maximum_weeks=estimated_maximum_weeks,
        schedule_status=schedule_status,
        items=response_items,
    )


def get_learning_schedule(
    resume_id: int,
    job_id: int,
    session: Session,
) -> LearningScheduleResponse:
    """Return a deterministic schedule projection without persistence."""
    resume = ResumeRepository(session).get_by_id(resume_id)

    if resume is None:
        raise ResumeNotFoundError("The requested resume was not found.")

    if JobRepository(session).get_by_id(job_id) is None:
        raise JobNotFoundError("The requested job was not found.")

    try:
        preferences = get_learning_preferences(
            user_id=resume.user_id,
            session=session,
        )
    except LearningPreferencesUserNotFoundError as error:
        raise ResumeNotFoundError(
            "The owner of the requested resume was not found."
        ) from error

    roadmap = build_learning_roadmap(
        resume_id=resume_id,
        job_id=job_id,
        session=session,
    )

    if roadmap is None:
        raise LearningRoadmapNotFoundError(
            "The learning roadmap was not found."
        )

    if (
        roadmap.resume_id != resume_id
        or roadmap.job_id != job_id
    ):
        raise LearningRoadmapNotFoundError(
            "The learning roadmap does not match the requested resume "
            "and job."
        )

    return _build_response(
        roadmap=roadmap,
        preferences=preferences,
    )
