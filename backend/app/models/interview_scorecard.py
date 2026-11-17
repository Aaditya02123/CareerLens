from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EvaluationStatus(str, Enum):
    COMPLETE = "complete"


class ScorecardStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    COMPLETE = "complete"


class ProviderCriterionEvaluation(BaseModel):
    criterion_id: str = Field(min_length=1)
    criterion_name: str = Field(min_length=1)
    score: int = Field(ge=0, le=5)
    explanation: str = Field(min_length=1, max_length=1000)
    evidence_excerpts: list[str] = Field(default_factory=list)
    improvement_suggestion: str = Field(min_length=1, max_length=1000)


class ProviderAnswerEvaluation(BaseModel):
    answer_id: int = Field(ge=1)
    question_id: int = Field(ge=1)
    competency_reference: str = Field(min_length=1)
    criterion_evaluations: list[ProviderCriterionEvaluation] = Field(
        min_length=1
    )
    strengths: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)
    actionable_feedback: list[str] = Field(default_factory=list)
    evaluation_status: Literal["complete"] = "complete"


class CriterionEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criterion_id: str
    criterion_name: str
    score: int = Field(ge=0, le=5)
    explanation: str
    evidence_excerpts: list[str] = Field(default_factory=list)
    improvement_suggestion: str


class AnswerEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    answer_id: int
    question_id: int
    question: str = ""
    answer: str = ""
    question_category: str = ""
    difficulty: str = ""
    question_order: int | None = None
    conversation_order: float | None = None
    is_follow_up: bool = False
    parent_question_id: int | None = None
    parent_question: str | None = None
    parent_answer: str | None = None
    competency_reference: str
    weighted_score: float = Field(ge=0.0, le=5.0)
    strengths: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)
    actionable_feedback: list[str] = Field(default_factory=list)
    evaluation_status: EvaluationStatus
    criteria: list[CriterionEvaluationResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    provider_name: str


class CompetencyScoreResponse(BaseModel):
    competency_reference: str
    competency_weight_percent: int = Field(ge=1, le=100)
    evaluated_answer_count: int = Field(ge=0)
    score: float = Field(ge=0.0, le=5.0)


class InterviewScorecardResponse(BaseModel):
    session_id: int
    status: ScorecardStatus
    overall_score: float | None = Field(default=None, ge=0.0, le=5.0)
    evaluated_answer_count: int = Field(ge=0)
    pending_answer_ids: list[int] = Field(default_factory=list)
    competency_scores: list[CompetencyScoreResponse] = Field(
        default_factory=list
    )
    answer_evaluations: list[AnswerEvaluationResponse] = Field(
        default_factory=list
    )
    strengths: list[str] = Field(default_factory=list)
    improvement_areas: list[str] = Field(default_factory=list)


class InterviewAnswerEvaluation(Base):
    __tablename__ = "interview_answer_evaluations"
    __table_args__ = (
        UniqueConstraint("answer_id", name="uq_interview_answer_evaluation_answer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_execution_sessions.id"), nullable=False, index=True
    )
    answer_id: Mapped[int] = mapped_column(
        ForeignKey("interview_execution_answers.id"), nullable=False, index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_session_questions.id"), nullable=False
    )
    competency_reference: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    weighted_score: Mapped[float] = mapped_column(
        Numeric(4, 2), nullable=False
    )
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    improvement_areas: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    actionable_feedback: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    evaluation_status: Mapped[EvaluationStatus] = mapped_column(
        SQLAlchemyEnum(EvaluationStatus, name="interview_evaluation_status"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    provider_name: Mapped[str] = mapped_column(
        String(120), nullable=False, default="unknown"
    )

    session = relationship(
        "InterviewExecutionSession",
        back_populates="evaluations",
    )
    answer = relationship(
        "InterviewSessionAnswer",
        back_populates="evaluation",
    )
    question = relationship(
        "InterviewSessionQuestion",
        back_populates="evaluations",
    )

    criteria: Mapped[list[CriterionEvaluation]] = relationship(
        "CriterionEvaluation",
        back_populates="evaluation",
        cascade="all, delete-orphan",
        order_by="CriterionEvaluation.id",
    )


class CriterionEvaluation(Base):
    __tablename__ = "interview_criterion_evaluations"
    __table_args__ = (
        UniqueConstraint(
            "evaluation_id",
            "criterion_id",
            name="uq_interview_criterion_evaluation",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    evaluation_id: Mapped[int] = mapped_column(
        ForeignKey("interview_answer_evaluations.id"), nullable=False, index=True
    )
    criterion_id: Mapped[str] = mapped_column(String(80), nullable=False)
    criterion_name: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_excerpts: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    improvement_suggestion: Mapped[str] = mapped_column(Text, nullable=False)

    evaluation: Mapped[InterviewAnswerEvaluation] = relationship(
        "InterviewAnswerEvaluation", back_populates="criteria"
    )


class InterviewScorecard(Base):
    __tablename__ = "interview_scorecards"
    __table_args__ = (
        UniqueConstraint("session_id", name="uq_interview_scorecard_session"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_execution_sessions.id"), nullable=False, index=True
    )
    status: Mapped[ScorecardStatus] = mapped_column(
        SQLAlchemyEnum(ScorecardStatus, name="interview_scorecard_status"),
        nullable=False,
    )
    overall_score: Mapped[float | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    evaluated_answer_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    pending_answer_ids: Mapped[list[int]] = mapped_column(
        JSON, nullable=False, default=list
    )
    competency_scores: Mapped[list[dict]] = mapped_column(
        JSON, nullable=False, default=list
    )
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    improvement_areas: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    session = relationship(
        "InterviewExecutionSession",
        back_populates="scorecard",
    )
