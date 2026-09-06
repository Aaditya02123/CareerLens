from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Job(Base):
    """Database model representing a job posting."""

    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "source_job_id",
            name="uq_jobs_source_source_job_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    company: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    responsibilities: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    required_skills: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    preferred_skills: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    experience_level: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    source_job_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class JobCreate(BaseModel):
    """Request schema for creating a job posting."""

    title: str
    company: str | None = None
    description: str
    responsibilities: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_level: str | None = None
    location: str | None = None
    source: str
    source_job_id: str | None = None
    source_url: str | None = None


class JobResponse(BaseModel):
    """Response schema for a job posting."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str | None
    description: str
    responsibilities: list[str]
    required_skills: list[str]
    preferred_skills: list[str]
    experience_level: str | None
    location: str | None
    source: str
    source_job_id: str | None
    source_url: str | None
    retrieved_at: datetime
    created_at: datetime