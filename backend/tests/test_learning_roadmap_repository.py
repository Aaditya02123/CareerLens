from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.learning_roadmap_db import (
    LearningRoadmap,
    LearningRoadmapItem,
)
from app.repositories.learning_roadmap_repository import (
    LearningRoadmapRepository,
)


class FakeSession:
    def __init__(
        self,
        *,
        commit_error=None,
        scalar_result=None,
    ):
        self.commit_error = commit_error
        self.scalar_result = scalar_result
        self.added = []
        self.refreshed = []
        self.rolled_back = False
        self.scalar_statements = []

    def add(self, value):
        self.added.append(value)

    def commit(self):
        if self.commit_error is not None:
            raise self.commit_error

    def rollback(self):
        self.rolled_back = True

    def refresh(self, value):
        self.refreshed.append(value)

    def scalar(self, statement):
        self.scalar_statements.append(statement)
        return self.scalar_result


def make_roadmap():
    return LearningRoadmap(
        id=10,
        resume_id=5,
        job_id=1,
    )


def make_item():
    return LearningRoadmapItem(
        id=20,
        roadmap_id=10,
        skill="SQL",
        skill_gap_status="missing",
        priority="high",
        reason="No matching resume evidence was found.",
        progress_status="not_started",
    )


def test_create_roadmap_persists_and_refreshes():
    session = FakeSession()
    repository = LearningRoadmapRepository(session)

    roadmap = repository.create(
        resume_id=5,
        job_id=1,
    )

    assert roadmap.resume_id == 5
    assert roadmap.job_id == 1
    assert session.added == [roadmap]
    assert session.refreshed == [roadmap]


def test_get_by_resume_and_job_returns_roadmap_with_items_loaded():
    roadmap = make_roadmap()
    session = FakeSession(scalar_result=roadmap)
    repository = LearningRoadmapRepository(session)

    result = repository.get_by_resume_and_job(
        resume_id=5,
        job_id=1,
    )

    assert result is roadmap
    assert session.scalar_statements

    compiled = str(session.scalar_statements[0]).upper()
    assert "LEARNING_ROADMAPS" in compiled
    assert "RESUME_ID" in compiled
    assert "JOB_ID" in compiled


def test_get_by_id_returns_roadmap():
    roadmap = make_roadmap()
    session = FakeSession(scalar_result=roadmap)
    repository = LearningRoadmapRepository(session)

    result = repository.get_by_id(roadmap_id=10)

    assert result is roadmap
    assert session.scalar_statements


def test_missing_roadmap_returns_none():
    session = FakeSession(scalar_result=None)
    repository = LearningRoadmapRepository(session)

    assert repository.get_by_id(roadmap_id=999) is None
    assert repository.get_by_resume_and_job(
        resume_id=5,
        job_id=1,
    ) is None


def test_add_item_preserves_roadmap_item_fields():
    roadmap = make_roadmap()
    session = FakeSession()
    repository = LearningRoadmapRepository(session)

    item = repository.add_item(
        roadmap=roadmap,
        skill="SQL",
        skill_gap_status="missing",
        priority="high",
        reason="No matching resume evidence was found.",
    )

    assert item.roadmap is roadmap
    assert item.skill == "SQL"
    assert item.skill_gap_status == "missing"
    assert item.priority == "high"
    assert item.reason == (
        "No matching resume evidence was found."
    )
    assert session.added == [item]
    assert session.refreshed == [item]


def test_multiple_items_belong_to_same_roadmap():
    roadmap = make_roadmap()
    session = FakeSession()
    repository = LearningRoadmapRepository(session)

    first = repository.add_item(
        roadmap=roadmap,
        skill="SQL",
        skill_gap_status="missing",
        priority="high",
        reason="SQL is missing.",
    )
    second = repository.add_item(
        roadmap=roadmap,
        skill="Docker",
        skill_gap_status="partial",
        priority="medium",
        reason="Related Docker evidence was found.",
    )

    assert first.roadmap is roadmap
    assert second.roadmap is roadmap
    assert first in roadmap.items
    assert second in roadmap.items


def test_get_item_by_id_returns_item():
    item = make_item()
    session = FakeSession(scalar_result=item)
    repository = LearningRoadmapRepository(session)

    result = repository.get_item_by_id(item_id=20)

    assert result is item
    assert session.scalar_statements


def test_update_item_progress_persists_supplied_value():
    item = make_item()
    session = FakeSession()
    repository = LearningRoadmapRepository(session)

    result = repository.update_item_progress(
        item=item,
        progress_status="in_progress",
    )

    assert result is item
    assert item.progress_status == "in_progress"
    assert session.refreshed == [item]


def test_create_rolls_back_and_reraises_database_error():
    error = IntegrityError(
        "duplicate roadmap",
        {},
        SimpleNamespace(),
    )
    session = FakeSession(commit_error=error)
    repository = LearningRoadmapRepository(session)

    with pytest.raises(IntegrityError) as raised:
        repository.create(
            resume_id=5,
            job_id=1,
        )

    assert raised.value is error
    assert session.rolled_back is True
    assert session.refreshed == []


def test_add_item_rolls_back_and_reraises_database_error():
    error = IntegrityError(
        "item insert failed",
        {},
        SimpleNamespace(),
    )
    session = FakeSession(commit_error=error)
    repository = LearningRoadmapRepository(session)

    with pytest.raises(IntegrityError) as raised:
        repository.add_item(
            roadmap=make_roadmap(),
            skill="SQL",
            skill_gap_status="missing",
            priority="high",
            reason="SQL is missing.",
        )

    assert raised.value is error
    assert session.rolled_back is True
    assert session.refreshed == []


def test_update_item_progress_rolls_back_and_reraises_database_error():
    error = IntegrityError(
        "progress update failed",
        {},
        SimpleNamespace(),
    )
    session = FakeSession(commit_error=error)
    repository = LearningRoadmapRepository(session)
    item = make_item()

    with pytest.raises(IntegrityError) as raised:
        repository.update_item_progress(
            item=item,
            progress_status="completed",
        )

    assert raised.value is error
    assert session.rolled_back is True
    assert session.refreshed == []


def test_duplicate_roadmap_database_error_is_not_swallowed():
    error = IntegrityError(
        "uq_learning_roadmaps_resume_job",
        {},
        SimpleNamespace(),
    )
    session = FakeSession(commit_error=error)
    repository = LearningRoadmapRepository(session)

    with pytest.raises(IntegrityError):
        repository.create(
            resume_id=5,
            job_id=1,
        )

    assert session.rolled_back is True