from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InterviewExecutionStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class InterviewExecutionSession(Base):
    __tablename__ = "interview_execution_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    blueprint_id: Mapped[int] = mapped_column(
        ForeignKey("interview_blueprints.id"), nullable=False, index=True
    )
    status: Mapped[InterviewExecutionStatus] = mapped_column(
        SQLAlchemyEnum(InterviewExecutionStatus, name="interview_execution_status"),
        nullable=False,
        default=InterviewExecutionStatus.CREATED,
    )
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    answered_questions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    questions: Mapped[list[InterviewSessionQuestion]] = relationship(
        "InterviewSessionQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewSessionQuestion.question_order",
    )
    answers: Mapped[list[InterviewSessionAnswer]] = relationship(
        "InterviewSessionAnswer",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewSessionAnswer.question_order",
    )


class InterviewSessionQuestion(Base):
    __tablename__ = "interview_session_questions"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "blueprint_question_id",
            name="uq_execution_session_blueprint_question",
        ),
        UniqueConstraint(
            "session_id",
            "question_order",
            name="uq_execution_session_question_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_execution_sessions.id"),
        nullable=False,
        index=True,
    )
    blueprint_question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_blueprint_questions.id"),
        nullable=False,
    )
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_category: Mapped[str] = mapped_column(String(40), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    target_competency: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_objective: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_reason: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped[InterviewExecutionSession] = relationship(
        "InterviewExecutionSession", back_populates="questions"
    )
    answers: Mapped[list[InterviewSessionAnswer]] = relationship(
        "InterviewSessionAnswer",
        back_populates="question_record",
        cascade="all, delete-orphan",
    )


class InterviewSessionAnswer(Base):
    __tablename__ = "interview_execution_answers"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "session_question_id",
            name="uq_execution_answer_session_question",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_execution_sessions.id"),
        nullable=False,
        index=True,
    )
    session_question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_session_questions.id"),
        nullable=False,
    )
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[InterviewExecutionSession] = relationship(
        "InterviewExecutionSession", back_populates="answers"
    )
    question_record: Mapped[InterviewSessionQuestion] = relationship(
        "InterviewSessionQuestion", back_populates="answers"
    )


class InterviewSessionAnswerCreate(BaseModel):
    answer: str = Field(min_length=1)


class InterviewSessionQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    blueprint_question_id: int
    question_order: int = Field(ge=1)
    question: str
    question_category: str
    difficulty: str
    target_competency: str
    assessment_objective: str
    relevance_reason: str


class InterviewSessionAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    session_question_id: int
    question_order: int
    answer: str
    submitted_at: datetime


class InterviewExecutionSessionResponse(BaseModel):
    id: int
    blueprint_id: int
    status: InterviewExecutionStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    total_questions: int = Field(ge=0)
    answered_questions: int = Field(ge=0)
    remaining_questions: int = Field(ge=0)
    completion_percentage: float = Field(ge=0.0, le=100.0)
    current_question_position: int | None = Field(default=None, ge=1)
    next_question: InterviewSessionQuestionResponse | None = None
    answers: list[InterviewSessionAnswerResponse] = Field(
        default_factory=list
    )
