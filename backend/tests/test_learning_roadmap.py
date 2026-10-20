from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.models.learning_roadmap import JobLearningRoadmapResponse
from app.models.skill_gap import SkillGapItem, SkillGapResponse
from app.services import learning_roadmap_service as service_module
from app.services.learning_roadmap_service import (
    build_learning_roadmap,
)


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


def make_persisted_item(
    *,
    item_id: int,
    skill: str,
    status: str,
    priority: str,
    reason: str,
    progress_status: str = "not_started",
):
    return SimpleNamespace(
        id=item_id,
        roadmap_id=20,
        skill=skill,
        skill_gap_status=status,
        priority=priority,
        reason=reason,
        progress_status=progress_status,
    )


def make_persisted_roadmap(items=None):
    return SimpleNamespace(
        id=20,
        resume_id=5,
        job_id=1,
        items=items or [],
    )


class FakeLearningRoadmapRepository:
    persisted_roadmap = None
    created_roadmaps = []
    added_items = []
    get_calls = []
    create_calls = []
    add_item_calls = []

    def __init__(self, session):
        self.session = session
        type(self).created_roadmaps = []
        type(self).added_items = []
        type(self).get_calls = []
        type(self).create_calls = []
        type(self).add_item_calls = []

    def get_by_resume_and_job(
        self,
        resume_id: int,
        job_id: int,
    ):
        type(self).get_calls.append(
            (resume_id, job_id)
        )
        return type(self).persisted_roadmap

    def create(
        self,
        resume_id: int,
        job_id: int,
    ):
        type(self).create_calls.append(
            (resume_id, job_id)
        )

        roadmap = make_persisted_roadmap()
        type(self).created_roadmaps.append(roadmap)
        return roadmap

    def add_item(
        self,
        roadmap,
        skill: str,
        skill_gap_status: str,
        priority: str,
        reason: str,
    ):
        type(self).add_item_calls.append(
            {
                "roadmap": roadmap,
                "skill": skill,
                "skill_gap_status": skill_gap_status,
                "priority": priority,
                "reason": reason,
            }
        )

        item = make_persisted_item(
            item_id=len(type(self).added_items) + 1,
            skill=skill,
            status=skill_gap_status,
            priority=priority,
            reason=reason,
        )
        roadmap.items.append(item)
        type(self).added_items.append(item)
        return item


@pytest.fixture
def fake_repository(monkeypatch):
    FakeLearningRoadmapRepository.persisted_roadmap = None

    monkeypatch.setattr(
        service_module,
        "LearningRoadmapRepository",
        FakeLearningRoadmapRepository,
    )

    return FakeLearningRoadmapRepository


def test_existing_persisted_roadmap_is_returned(
    monkeypatch,
    fake_repository,
):
    persisted = make_persisted_roadmap(
        [
            make_persisted_item(
                item_id=1,
                skill="SQL",
                status="missing",
                priority="high",
                reason="SQL is missing.",
                progress_status="in_progress",
            ),
            make_persisted_item(
                item_id=2,
                skill="Docker",
                status="partial",
                priority="medium",
                reason="Docker has partial evidence.",
                progress_status="completed",
            ),
        ]
    )
    fake_repository.persisted_roadmap = persisted

    mocked_get_skill_gap = Mock(
        side_effect=AssertionError(
            "get_skill_gap must not be called"
        )
    )

    monkeypatch.setattr(
        service_module,
        "get_skill_gap",
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
    assert result.roadmap[0].status == "missing"
    assert result.roadmap[0].priority == "high"
    assert result.roadmap[0].reason == "SQL is missing."
    assert result.roadmap[0].progress_status == "in_progress"
    assert result.roadmap[1].progress_status == "completed"

    mocked_get_skill_gap.assert_not_called()


@pytest.mark.parametrize(
    "progress_status",
    [
        "in_progress",
        "completed",
    ],
)
def test_persisted_progress_status_is_returned(
    monkeypatch,
    fake_repository,
    progress_status,
):
    persisted = make_persisted_roadmap(
        [
            make_persisted_item(
                item_id=1,
                skill="SQL",
                status="missing",
                priority="high",
                reason="SQL is missing.",
                progress_status=progress_status,
            ),
        ]
    )
    fake_repository.persisted_roadmap = persisted

    monkeypatch.setattr(
        service_module,
        "get_skill_gap",
        Mock(
            side_effect=AssertionError(
                "persisted roadmaps must not be regenerated"
            )
        ),
    )

    result = build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert result.roadmap[0].progress_status == progress_status


def test_existing_items_are_not_regenerated_or_overwritten(
    monkeypatch,
    fake_repository,
):
    persisted = make_persisted_roadmap(
        [
            make_persisted_item(
                item_id=1,
                skill="Docker",
                status="missing",
                priority="high",
                reason="Docker is missing.",
                progress_status="completed",
            ),
        ]
    )
    fake_repository.persisted_roadmap = persisted

    mocked_get_skill_gap = Mock()
    monkeypatch.setattr(
        service_module,
        "get_skill_gap",
        mocked_get_skill_gap,
    )

    result = build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert [item.skill for item in result.roadmap] == [
        "Docker",
    ]
    assert result.roadmap[0].progress_status == "completed"
    assert persisted.items[0].progress_status == "completed"
    assert fake_repository.create_calls == []
    assert fake_repository.add_item_calls == []
    mocked_get_skill_gap.assert_not_called()


def test_new_roadmap_is_generated_when_none_exists(
    monkeypatch,
    fake_repository,
):
    skill_gap = make_skill_gap(
        partial=[
            make_skill(
                "PostgreSQL",
                "partial",
                "medium",
                "Related PostgreSQL evidence was found.",
            ),
        ],
        missing=[
            make_skill(
                "Docker",
                "missing",
                "high",
                "Docker is missing from the resume.",
            ),
        ],
    )

    mocked_get_skill_gap = Mock(return_value=skill_gap)

    monkeypatch.setattr(
        service_module,
        "get_skill_gap",
        mocked_get_skill_gap,
    )

    result = build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert result.total_items == 2
    assert [item.skill for item in result.roadmap] == [
        "PostgreSQL",
        "Docker",
    ]
    assert [
        item.progress_status
        for item in result.roadmap
    ] == [
        "not_started",
        "not_started",
    ]

    assert fake_repository.create_calls == [(5, 1)]
    assert len(fake_repository.add_item_calls) == 2
    assert all(
    item.progress_status == "not_started"
    for item in result.roadmap
    )
    mocked_get_skill_gap.assert_called_once()


def test_partial_skills_are_persisted_with_medium_priority(
    monkeypatch,
    fake_repository,
):
    skill_gap = make_skill_gap(
        partial=[
            make_skill(
                "PostgreSQL",
                "partial",
                "medium",
                "Related PostgreSQL evidence was found.",
            ),
        ],
    )

    monkeypatch.setattr(
        service_module,
        "get_skill_gap",
        Mock(return_value=skill_gap),
    )

    build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert fake_repository.add_item_calls == [
        {
            "roadmap": fake_repository.created_roadmaps[0],
            "skill": "PostgreSQL",
            "skill_gap_status": "partial",
            "priority": "medium",
            "reason": (
                "Required skill has partial supporting evidence "
                "in the resume."
            ),
        }
    ]


def test_missing_skills_are_persisted_with_high_priority(
    monkeypatch,
    fake_repository,
):
    skill_gap = make_skill_gap(
        missing=[
            make_skill(
                "SQL",
                "missing",
                "high",
                "SQL is missing from the resume.",
            ),
        ],
    )

    monkeypatch.setattr(
        service_module,
        "get_skill_gap",
        Mock(return_value=skill_gap),
    )

    build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert fake_repository.add_item_calls[0][
        "skill_gap_status"
    ] == "missing"
    assert fake_repository.add_item_calls[0][
        "priority"
    ] == "high"
    assert fake_repository.add_item_calls[0][
        "reason"
    ] == "Required skill is missing from the resume."


def test_matched_skills_are_excluded_from_persistence(
    monkeypatch,
    fake_repository,
):
    skill_gap = make_skill_gap(
        matched=[
            make_skill(
                "FastAPI",
                "matched",
                "low",
                "FastAPI is directly matched.",
            ),
        ],
        missing=[
            make_skill(
                "SQL",
                "missing",
                "high",
                "SQL is missing from the resume.",
            ),
        ],
    )

    monkeypatch.setattr(
        service_module,
        "get_skill_gap",
        Mock(return_value=skill_gap),
    )

    result = build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert [item.skill for item in result.roadmap] == ["SQL"]
    assert [
        call["skill"]
        for call in fake_repository.add_item_calls
    ] == ["SQL"]


def test_partial_items_precede_missing_items(
    monkeypatch,
    fake_repository,
):
    skill_gap = make_skill_gap(
        partial=[
            make_skill(
                "PostgreSQL",
                "partial",
                "medium",
                "PostgreSQL has related evidence.",
            ),
        ],
        missing=[
            make_skill(
                "Docker",
                "missing",
                "high",
                "Docker is missing.",
            ),
            make_skill(
                "Redis",
                "missing",
                "high",
                "Redis is missing.",
            ),
        ],
    )

    monkeypatch.setattr(
        service_module,
        "get_skill_gap",
        Mock(return_value=skill_gap),
    )

    result = build_learning_roadmap(
        resume_id=5,
        job_id=1,
        session=Mock(),
    )

    assert [item.skill for item in result.roadmap] == [
        "PostgreSQL",
        "Docker",
        "Redis",
    ]

    assert [
        call["skill"]
        for call in fake_repository.add_item_calls
    ] == [
        "PostgreSQL",
        "Docker",
        "Redis",
    ]


def test_empty_skill_gap_persists_empty_roadmap(
    monkeypatch,
    fake_repository,
):
    skill_gap = make_skill_gap()

    monkeypatch.setattr(
        service_module,
        "get_skill_gap",
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
    assert fake_repository.create_calls == [(5, 1)]
    assert fake_repository.add_item_calls == []


def test_repository_error_propagates(
    monkeypatch,
):
    repository_error = RuntimeError("repository failed")

    class ErrorRepository:
        def __init__(self, session):
            pass

        def get_by_resume_and_job(
            self,
            resume_id,
            job_id,
        ):
            raise repository_error

    monkeypatch.setattr(
        service_module,
        "LearningRoadmapRepository",
        ErrorRepository,
    )

    mocked_get_skill_gap = Mock()
    monkeypatch.setattr(
        service_module,
        "get_skill_gap",
        mocked_get_skill_gap,
    )

    with pytest.raises(RuntimeError, match="repository failed"):
        build_learning_roadmap(
            resume_id=5,
            job_id=1,
            session=Mock(),
        )

    mocked_get_skill_gap.assert_not_called()


def test_skill_gap_exception_propagates_unchanged(
    monkeypatch,
    fake_repository,
):
    expected_error = RuntimeError("Skill gap analysis failed.")

    monkeypatch.setattr(
        service_module,
        "get_skill_gap",
        Mock(side_effect=expected_error),
    )

    with pytest.raises(RuntimeError, match="Skill gap analysis failed."):
        build_learning_roadmap(
            resume_id=5,
            job_id=1,
            session=Mock(),
        )