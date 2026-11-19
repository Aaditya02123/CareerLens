from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


InterviewType = Literal["technical", "behavioral", "project_based", "mixed"]
BlueprintDifficulty = Literal["easy", "medium", "hard", "adaptive"]
QuestionCategory = Literal[
    "technical",
    "project_based",
    "resume_based",
    "behavioral",
    "scenario_based",
    "problem_solving",
]
QuestionDifficulty = Literal["easy", "medium", "hard"]
RubricCategory = Literal[
    "technical",
    "project_based",
    "resume_based",
    "behavioral",
    "scenario_based",
    "problem_solving",
    "communication",
]


class BlueprintCompetencyDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: str = Field(min_length=1)
    weight_percent: int = Field(ge=1, le=100)
    related_job_requirements: list[str] = Field(default_factory=list)
    related_resume_evidence: list[str] = Field(default_factory=list)
    assessment_objectives: list[str] = Field(default_factory=list)


class BlueprintQuestionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    category: QuestionCategory
    difficulty: QuestionDifficulty
    target_competency: str = Field(min_length=1)
    assessment_objective: str = Field(min_length=1)
    relevance_reason: str = Field(min_length=1)
    supporting_job_requirement: str | None = None
    supporting_resume_evidence: str | None = None
    expected_answer_topics: list[str] = Field(default_factory=list)
    rubric_criteria: list[str] = Field(default_factory=list)
    estimated_response_seconds: int = Field(ge=15, le=600)
    follow_up_allowed: bool = False


class BlueprintRubricCriterionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: RubricCategory
    description: str = Field(min_length=1)
    weight_percent: int = Field(ge=1, le=100)
    scale_min: int = Field(default=0, ge=0, le=5)
    scale_max: int = Field(default=5, ge=0, le=5)
    scoring_guidance: list[str] = Field(min_length=1)
    evidence_expectations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_scale(self) -> "BlueprintRubricCriterionDraft":
        if self.scale_max <= self.scale_min:
            raise ValueError("scale_max must be greater than scale_min.")
        return self


class InterviewBlueprintGenerationPayload(BaseModel):
    """Strict provider output used before a blueprint is persisted."""

    model_config = ConfigDict(extra="forbid")

    target_role: str = Field(min_length=1)
    interview_type: InterviewType
    difficulty: BlueprintDifficulty
    duration_minutes: int = Field(ge=5, le=180)
    question_count: int = Field(ge=1, le=30)
    competencies: list[BlueprintCompetencyDraft] = Field(min_length=1)
    questions: list[BlueprintQuestionDraft] = Field(min_length=1)
    rubric: list[BlueprintRubricCriterionDraft] = Field(min_length=1)


class InterviewBlueprintConfig(BaseModel):
    """Validated options for one blueprint generation request."""

    interview_type: InterviewType = "mixed"
    duration_minutes: int = Field(default=30, ge=5, le=180)
    question_count: int = Field(default=10, ge=1, le=30)
    difficulty: BlueprintDifficulty = "adaptive"
    focus_competencies: list[str] = Field(default_factory=list)


class BlueprintCompetencyResponse(BlueprintCompetencyDraft):
    model_config = ConfigDict(from_attributes=True)

    id: int
    blueprint_id: int


class BlueprintQuestionResponse(BlueprintQuestionDraft):
    model_config = ConfigDict(from_attributes=True)

    id: int
    blueprint_id: int
    question_order: int = Field(ge=1)


class BlueprintRubricCriterionResponse(BlueprintRubricCriterionDraft):
    model_config = ConfigDict(from_attributes=True)

    id: int
    blueprint_id: int


class InterviewBlueprintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    job_id: int
    target_role: str
    interview_type: InterviewType
    difficulty: BlueprintDifficulty
    duration_minutes: int
    question_count: int
    created_at: datetime
    competencies: list[BlueprintCompetencyResponse] = Field(
        default_factory=list
    )
    questions: list[BlueprintQuestionResponse] = Field(default_factory=list)
    rubric: list[BlueprintRubricCriterionResponse] = Field(
        default_factory=list
    )


class InterviewBlueprint(Base):
    __tablename__ = "interview_blueprints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id"), nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"), nullable=False, index=True
    )
    target_role: Mapped[str] = mapped_column(String(255), nullable=False)
    interview_type: Mapped[str] = mapped_column(String(30), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    competencies: Mapped[list[BlueprintCompetency]] = relationship(
        "BlueprintCompetency",
        back_populates="blueprint",
        cascade="all, delete-orphan",
        order_by="BlueprintCompetency.id",
    )
    questions: Mapped[list[BlueprintQuestion]] = relationship(
        "BlueprintQuestion",
        back_populates="blueprint",
        cascade="all, delete-orphan",
        order_by="BlueprintQuestion.question_order",
    )
    rubric: Mapped[list[BlueprintRubricCriterion]] = relationship(
        "BlueprintRubricCriterion",
        back_populates="blueprint",
        cascade="all, delete-orphan",
        order_by="BlueprintRubricCriterion.id",
    )


class BlueprintCompetency(Base):
    __tablename__ = "interview_blueprint_competencies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    blueprint_id: Mapped[int] = mapped_column(
        ForeignKey("interview_blueprints.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    weight_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    related_job_requirements: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    related_resume_evidence: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    assessment_objectives: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    blueprint: Mapped[InterviewBlueprint] = relationship(
        "InterviewBlueprint", back_populates="competencies"
    )


class BlueprintQuestion(Base):
    __tablename__ = "interview_blueprint_questions"
    __table_args__ = (
        UniqueConstraint("blueprint_id", "question_id", name="uq_blueprint_question_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    blueprint_id: Mapped[int] = mapped_column(
        ForeignKey("interview_blueprints.id"), nullable=False, index=True
    )
    question_id: Mapped[str] = mapped_column(String(80), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    target_competency: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_objective: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_reason: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_job_requirement: Mapped[str | None] = mapped_column(Text)
    supporting_resume_evidence: Mapped[str | None] = mapped_column(Text)
    expected_answer_topics: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    rubric_criteria: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    estimated_response_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    follow_up_allowed: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    blueprint: Mapped[InterviewBlueprint] = relationship(
        "InterviewBlueprint", back_populates="questions"
    )


class BlueprintRubricCriterion(Base):
    __tablename__ = "interview_blueprint_rubric_criteria"
    __table_args__ = (
        UniqueConstraint("blueprint_id", "criterion_id", name="uq_blueprint_criterion_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    blueprint_id: Mapped[int] = mapped_column(
        ForeignKey("interview_blueprints.id"), nullable=False, index=True
    )
    criterion_id: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    weight_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    scale_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scale_max: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    scoring_guidance: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    evidence_expectations: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    blueprint: Mapped[InterviewBlueprint] = relationship(
        "InterviewBlueprint", back_populates="rubric"
    )
