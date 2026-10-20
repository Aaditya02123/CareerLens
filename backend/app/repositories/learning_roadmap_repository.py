from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.learning_roadmap_db import (
    LearningRoadmap,
    LearningRoadmapItem,
)


class LearningRoadmapRepository:
    """Persistence operations for learning roadmaps and roadmap items."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_resume_and_job(
        self,
        resume_id: int,
        job_id: int,
    ) -> LearningRoadmap | None:
        """Return the roadmap for a resume/job pair, if it exists."""
        statement = (
            select(LearningRoadmap)
            .options(selectinload(LearningRoadmap.items))
            .where(
                LearningRoadmap.resume_id == resume_id,
                LearningRoadmap.job_id == job_id,
            )
        )

        return self.session.scalar(statement)

    def get_by_id(
        self,
        roadmap_id: int,
    ) -> LearningRoadmap | None:
        """Return a roadmap by ID, if it exists."""
        statement = (
            select(LearningRoadmap)
            .options(selectinload(LearningRoadmap.items))
            .where(LearningRoadmap.id == roadmap_id)
        )

        return self.session.scalar(statement)

    def create(
        self,
        resume_id: int,
        job_id: int,
    ) -> LearningRoadmap:
        """Create and persist a roadmap record."""
        roadmap = LearningRoadmap(
            resume_id=resume_id,
            job_id=job_id,
        )

        self.session.add(roadmap)

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(roadmap)
        return roadmap

    def add_item(
        self,
        roadmap: LearningRoadmap,
        skill: str,
        skill_gap_status: str,
        priority: str,
        reason: str,
    ) -> LearningRoadmapItem:
        """Create and persist an item belonging to a roadmap."""
        item = LearningRoadmapItem(
            roadmap=roadmap,
            skill=skill,
            skill_gap_status=skill_gap_status,
            priority=priority,
            reason=reason,
        )

        self.session.add(item)

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(item)
        return item

    def get_item_by_id(
        self,
        item_id: int,
    ) -> LearningRoadmapItem | None:
        """Return a roadmap item by ID, if it exists."""
        statement = select(LearningRoadmapItem).where(
            LearningRoadmapItem.id == item_id
        )

        return self.session.scalar(statement)

    def update_item_progress(
        self,
        item: LearningRoadmapItem,
        progress_status: str,
    ) -> LearningRoadmapItem:
        """Persist a supplied roadmap-item progress status."""
        item.progress_status = progress_status

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(item)
        return item