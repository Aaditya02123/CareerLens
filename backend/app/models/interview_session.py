from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.jobs import Job
    from app.models.resume import Resume
    from app.models.user import User


class InterviewSessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InterviewSession(Base):
    """Database model for one mock-interview attempt."""

    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
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

    status: Mapped[InterviewSessionStatus] = mapped_column(
        SQLAlchemyEnum(
            InterviewSessionStatus,
            name="interview_session_status",
        ),
        nullable=False,
        default=InterviewSessionStatus.ACTIVE,
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

    user: Mapped[User] = relationship("User")
    resume: Mapped[Resume] = relationship("Resume")
    job: Mapped[Job] = relationship("Job")

    answers: Mapped[list[InterviewAnswer]] = relationship(
        "InterviewAnswer",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class InterviewAnswer(Base):
    """Database model for one submitted interview answer."""

    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id"),
        nullable=False,
        index=True,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    question_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped[InterviewSession] = relationship(
        "InterviewSession",
        back_populates="answers",
    )


class InterviewSessionCreate(BaseModel):
    """Request schema for creating an interview session."""

    user_id: int
    resume_id: int
    job_id: int


class InterviewAnswerCreate(BaseModel):
    """Request schema for submitting an interview answer."""

    question: str
    answer: str
    question_category: Literal[
        "technical",
        "resume_based",
        "behavioral",
        "job_specific",
    ]


class InterviewAnswerResponse(BaseModel):
    """Response schema for an interview answer."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    question: str
    answer: str
    question_category: Literal[
        "technical",
        "resume_based",
        "behavioral",
        "job_specific",
    ]
    created_at: datetime


class InterviewSessionResponse(BaseModel):
    """Response schema for an interview session."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    resume_id: int
    job_id: int
    status: InterviewSessionStatus
    created_at: datetime
    updated_at: datetime
    answers: list[InterviewAnswerResponse] = Field(
        default_factory=list
    )