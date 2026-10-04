from unittest.mock import Mock

import pytest

from app.models.learning_roadmap import JobLearningRoadmapResponse
from app.models.skill_gap import SkillGapItem, SkillGapResponse
from app.services.learning_roadmap_service import build_learning_roadmap


def make_skill_gap(
    *,
    matched=None,
    partial=None,
    missing=None,
) -> SkillGapResponse:
    matched = matched or []
    partial = partial or []
    missing = missing or []

    return SkillGapResponse(
        resume_id=5,
        job_id=1,
        total_required_skills=len(matched) + len(partial) + len(missing),
        matched_count=len(matched),
        partial_count=len(partial),
        missing_count=len(missing),
        matched=matched,
        partial=partial,
        missing=missing,
    )


def make_skill(
    skill: str,
    status: str,
    priority: str,
    reason: str,
) -> SkillGapItem:
    return SkillGapItem(
        skill=skill,
        status=status,
        priority=priority,
        reason=reason,
        evidence=[],
    )


def test_missing_skills_become_high_priority_roadmap_items(monkeypatch):
    skill_gap = make_skill_gap(
        missing=[
            make_skill(
                "SQL",
                "missing",
                "high",
                "No matching or supporting resume evidence was found.",
            ),
            make_skill(
                "Docker",
                "missing",
                "high",
                "No matching or supporting resume evidence was found.",
            ),
        ]
    )

    mocked_get_skill_gap = Mock(return_value=skill_gap)

    monkeypatch.setattr(
        "app.services.learning_roadmap_service.get_skill_gap",
        mocked_get_skill_gap,
    )

    result = build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert isinstance(result, JobLearningRoadmapResponse)
    assert result.resume_id == 5
    assert result.job_id == 1
    assert result.total_items == 2

    assert [item.skill for item in result.roadmap] == [
        "SQL",
        "Docker",
    ]

    assert all(item.status == "missing" for item in result.roadmap)
    assert all(item.priority == "high" for item in result.roadmap)

    mocked_get_skill_gap.assert_called_once()
    call_kwargs = mocked_get_skill_gap.call_args.kwargs

    assert call_kwargs["resume_id"] == 5
    assert call_kwargs["job_id"] == 1
    assert call_kwargs["session"] is not None


def test_partial_skills_become_medium_priority_roadmap_items(monkeypatch):
    skill_gap = make_skill_gap(
        partial=[
            make_skill(
                "Python",
                "partial",
                "medium",
                "Required skill has partial supporting evidence in the resume.",
            ),
            make_skill(
                "PostgreSQL",
                "partial",
                "medium",
                "Required skill has partial supporting evidence in the resume.",
            ),
        ]
    )

    monkeypatch.setattr(
        "app.services.learning_roadmap_service.get_skill_gap",
        Mock(return_value=skill_gap),
    )

    result = build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert result.total_items == 2

    assert [item.skill for item in result.roadmap] == [
        "Python",
        "PostgreSQL",
    ]

    assert all(item.status == "partial" for item in result.roadmap)
    assert all(item.priority == "medium" for item in result.roadmap)


def test_matched_skills_are_excluded_from_roadmap(monkeypatch):
    skill_gap = make_skill_gap(
        matched=[
            make_skill(
                "FastAPI",
                "matched",
                "low",
                "Required skill is directly matched by the resume.",
            ),
            make_skill(
                "Python",
                "matched",
                "low",
                "Required skill is directly matched by the resume.",
            ),
        ]
    )

    monkeypatch.setattr(
        "app.services.learning_roadmap_service.get_skill_gap",
        Mock(return_value=skill_gap),
    )

    result = build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert result.total_items == 0
    assert result.roadmap == []


def test_mixed_skill_gap_creates_partial_then_missing_items(monkeypatch):
    skill_gap = make_skill_gap(
        matched=[
            make_skill(
                "FastAPI",
                "matched",
                "low",
                "Required skill is directly matched by the resume.",
            )
        ],
        partial=[
            make_skill(
                "PostgreSQL",
                "partial",
                "medium",
                "Required skill has partial supporting evidence in the resume.",
            )
        ],
        missing=[
            make_skill(
                "Docker",
                "missing",
                "high",
                "No matching or supporting resume evidence was found.",
            ),
            make_skill(
                "Redis",
                "missing",
                "high",
                "No matching or supporting resume evidence was found.",
            ),
        ],
    )

    monkeypatch.setattr(
        "app.services.learning_roadmap_service.get_skill_gap",
        Mock(return_value=skill_gap),
    )

    result = build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert result.total_items == 3

    assert [item.skill for item in result.roadmap] == [
        "PostgreSQL",
        "Docker",
        "Redis",
    ]

    assert result.roadmap[0].status == "partial"
    assert result.roadmap[0].priority == "medium"

    assert result.roadmap[1].status == "missing"
    assert result.roadmap[1].priority == "high"

    assert result.roadmap[2].status == "missing"
    assert result.roadmap[2].priority == "high"

    assert "FastAPI" not in [item.skill for item in result.roadmap]


def test_empty_skill_gap_returns_empty_roadmap(monkeypatch):
    skill_gap = make_skill_gap()

    monkeypatch.setattr(
        "app.services.learning_roadmap_service.get_skill_gap",
        Mock(return_value=skill_gap),
    )

    result = build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert result.resume_id == 5
    assert result.job_id == 1
    assert result.total_items == 0
    assert result.roadmap == []


def test_skill_gap_exception_is_propagated(monkeypatch):
    expected_error = RuntimeError("Skill gap analysis failed.")

    mocked_get_skill_gap = Mock(side_effect=expected_error)

    monkeypatch.setattr(
        "app.services.learning_roadmap_service.get_skill_gap",
        mocked_get_skill_gap,
    )

    with pytest.raises(RuntimeError, match="Skill gap analysis failed."):
        build_learning_roadmap(
            resume_id=5,
            job_id=1,
            session=Mock(),
        )

    mocked_get_skill_gap.assert_called_once()