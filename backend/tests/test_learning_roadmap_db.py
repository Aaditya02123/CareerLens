from sqlalchemy import inspect

from app.models.learning_roadmap_db import (
    LearningRoadmap,
    LearningRoadmapItem,
)


def test_learning_roadmap_can_be_instantiated():
    roadmap = LearningRoadmap(
        resume_id=5,
        job_id=1,
    )

    assert roadmap.resume_id == 5
    assert roadmap.job_id == 1
    assert roadmap.items == []


def test_learning_roadmap_item_has_expected_fields_and_default():
    item = LearningRoadmapItem(
        roadmap_id=10,
        skill="SQL",
        skill_gap_status="missing",
        priority="high",
        reason="No matching or supporting resume evidence was found.",
    )

    assert item.roadmap_id == 10
    assert item.skill == "SQL"
    assert item.skill_gap_status == "missing"
    assert item.priority == "high"
    assert item.reason == (
        "No matching or supporting resume evidence was found."
    )

    progress_column = LearningRoadmapItem.__table__.c.progress_status
    assert progress_column.default.arg == "not_started"


def test_progress_status_supports_expected_values():
    for status in [
        "not_started",
        "in_progress",
        "completed",
    ]:
        item = LearningRoadmapItem(
            roadmap_id=1,
            skill="Python",
            skill_gap_status="partial",
            priority="medium",
            reason="Related resume evidence was found.",
            progress_status=status,
        )

        assert item.progress_status == status


def test_roadmap_items_relationship_works():
    roadmap = LearningRoadmap(
        resume_id=5,
        job_id=1,
    )

    item = LearningRoadmapItem(
        skill="FastAPI",
        skill_gap_status="partial",
        priority="medium",
        reason="Related resume evidence was found.",
    )

    roadmap.items.append(item)

    assert roadmap.items == [item]
    assert item.roadmap is roadmap


def test_roadmap_items_relationship_uses_delete_orphan_cascade():
    relationship = inspect(LearningRoadmap).relationships["items"]

    assert "delete-orphan" in relationship.cascade
    assert "delete" in relationship.cascade


def test_roadmap_has_resume_job_unique_constraint():
    constraints = LearningRoadmap.__table__.constraints

    assert any(
        constraint.name == "uq_learning_roadmaps_resume_job"
        for constraint in constraints
    )


def test_foreign_keys_target_existing_tables():
    roadmap_foreign_keys = {
        foreign_key.target_fullname
        for column in LearningRoadmap.__table__.columns
        for foreign_key in column.foreign_keys
    }

    item_foreign_keys = {
        foreign_key.target_fullname
        for column in LearningRoadmapItem.__table__.columns
        for foreign_key in column.foreign_keys
    }

    assert "resumes.id" in roadmap_foreign_keys
    assert "jobs.id" in roadmap_foreign_keys
    assert "learning_roadmaps.id" in item_foreign_keys