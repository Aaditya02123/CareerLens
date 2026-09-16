from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import (
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
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


QuestionCategory = Literal[
    "technical",
    "resume_based",
    "behavioral",
    "job_specific",
]
QuestionDifficulty = Literal["easy", "medium", "hard"]
QuestionPriority = Literal["high", "medium", "low"]


class InterviewSessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id"), nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"), nullable=False, index=True
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
    questions: Mapped[list[InterviewQuestion]] = relationship(
        "InterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.question_order",
    )
    answers: Mapped[list[InterviewAnswer]] = relationship(
        "InterviewAnswer",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    difficulty: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    question_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped[InterviewSession] = relationship(
        "InterviewSession",
        back_populates="questions",
    )
    answers: Mapped[list[InterviewAnswer]] = relationship(
        "InterviewAnswer",
        back_populates="question_record",
        cascade="all, delete-orphan",
    )


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_questions.id"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
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
    question_record: Mapped[InterviewQuestion] = relationship(
        "InterviewQuestion",
        back_populates="answers",
    )


class InterviewSessionCreate(BaseModel):
    user_id: int
    resume_id: int
    job_id: int


class InterviewAnswerCreate(BaseModel):
    question_id: int
    answer: str


class InterviewQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    question: str
    question_category: QuestionCategory
    difficulty: QuestionDifficulty
    priority: QuestionPriority
    reason: str
    question_order: int
    created_at: datetime


class InterviewAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    question_id: int
    question: str
    answer: str
    question_category: QuestionCategory
    created_at: datetime


class InterviewSessionResponse(BaseModel):
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