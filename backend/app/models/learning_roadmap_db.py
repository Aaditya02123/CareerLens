from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LearningRoadmap(Base):
    """Persisted learning roadmap for one resume and job pair."""

    __tablename__ = "learning_roadmaps"
    __table_args__ = (
        UniqueConstraint(
            "resume_id",
            "job_id",
            name="uq_learning_roadmaps_resume_job",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id"),
        nullable=False,
        index=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items: Mapped[list[LearningRoadmapItem]] = relationship(
        "LearningRoadmapItem",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="LearningRoadmapItem.id",
    )


class LearningRoadmapItem(Base):
    """Persisted learning item derived from a skill gap."""

    __tablename__ = "learning_roadmap_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    roadmap_id: Mapped[int] = mapped_column(
        ForeignKey("learning_roadmaps.id"),
        nullable=False,
        index=True,
    )

    skill: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    skill_gap_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    progress_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="not_started",
        server_default="not_started",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    roadmap: Mapped[LearningRoadmap] = relationship(
        "LearningRoadmap",
        back_populates="items",
    )