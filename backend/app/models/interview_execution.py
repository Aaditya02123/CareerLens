from __future__ import annotations

from datetime import datetime
from enum import Enum
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InterviewExecutionStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


AdaptiveDecisionOutcome = Literal["ask_follow_up", "continue"]
AdaptiveFollowUpType = Literal[
    "technical_clarification",
    "deeper_exploration",
    "project_exploration",
    "problem_solving",
]


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
    evaluations: Mapped[list["InterviewAnswerEvaluation"]] = relationship(
        "InterviewAnswerEvaluation",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    scorecard: Mapped["InterviewScorecard | None"] = relationship(
        "InterviewScorecard",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
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
    blueprint_question_id: Mapped[int | None] = mapped_column(
        ForeignKey("interview_blueprint_questions.id"),
        nullable=True,
    )
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_category: Mapped[str] = mapped_column(String(40), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    target_competency: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_objective: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_reason: Mapped[str] = mapped_column(Text, nullable=False)
    rubric_criteria: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    is_follow_up: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )
    parent_question_id: Mapped[int | None] = mapped_column(
        ForeignKey("interview_session_questions.id"), nullable=True
    )
    conversation_order: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), nullable=False
    )

    session: Mapped[InterviewExecutionSession] = relationship(
        "InterviewExecutionSession", back_populates="questions"
    )
    answers: Mapped[list[InterviewSessionAnswer]] = relationship(
        "InterviewSessionAnswer",
        back_populates="question_record",
        cascade="all, delete-orphan",
    )
    evaluations: Mapped[list["InterviewAnswerEvaluation"]] = relationship(
        "InterviewAnswerEvaluation",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    parent_question: Mapped[InterviewSessionQuestion | None] = relationship(
        "InterviewSessionQuestion",
        remote_side="InterviewSessionQuestion.id",
        back_populates="follow_ups",
    )
    follow_ups: Mapped[list[InterviewSessionQuestion]] = relationship(
        "InterviewSessionQuestion",
        back_populates="parent_question",
        foreign_keys=[parent_question_id],
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
    conversation_order: Mapped[Decimal] = mapped_column(
        Numeric(10, 3), nullable=False
    )
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
    evaluation: Mapped["InterviewAnswerEvaluation | None"] = relationship(
        "InterviewAnswerEvaluation",
        back_populates="answer",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )


class InterviewAdaptiveDecision(Base):
    __tablename__ = "interview_adaptive_decisions"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "parent_question_id",
            name="uq_adaptive_decision_session_parent",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_execution_sessions.id"),
        nullable=False,
        index=True,
    )
    parent_question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_session_questions.id"), nullable=False
    )
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    follow_up_type: Mapped[str | None] = mapped_column(String(40))
    competency_reference: Mapped[str | None] = mapped_column(String(255))
    follow_up_question_id: Mapped[int | None] = mapped_column(
        ForeignKey("interview_session_questions.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InterviewSessionAnswerCreate(BaseModel):
    answer: str = Field(min_length=1)


class InterviewSessionQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    blueprint_question_id: int | None
    question_order: int = Field(ge=1)
    question: str
    question_category: str
    difficulty: str
    target_competency: str
    assessment_objective: str
    relevance_reason: str
    is_follow_up: bool
    parent_question_id: int | None
    conversation_order: float


class InterviewSessionAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    session_question_id: int
    question_order: int
    conversation_order: float
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


class AdaptiveDecisionPayload(BaseModel):
    outcome: AdaptiveDecisionOutcome
    rationale: str = Field(min_length=1, max_length=1000)
    follow_up_question: str | None = Field(default=None, min_length=10, max_length=500)
    follow_up_type: AdaptiveFollowUpType | None = None
    competency_reference: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_follow_up_fields(self) -> "AdaptiveDecisionPayload":
        if self.outcome == "ask_follow_up":
            if self.follow_up_question is None or self.follow_up_type is None:
                raise ValueError(
                    "ask_follow_up decisions require a question and type."
                )
        elif any(
            value is not None
            for value in (
                self.follow_up_question,
                self.follow_up_type,
            )
        ):
            raise ValueError(
                "continue decisions cannot include follow-up fields."
            )
        return self


class AdaptiveDecisionResponse(BaseModel):
    session_id: int
    parent_question_id: int
    outcome: AdaptiveDecisionOutcome
    follow_up_question: InterviewSessionQuestionResponse | None = None


class AdaptiveDecisionRequest(BaseModel):
    parent_question_id: int = Field(ge=1)
