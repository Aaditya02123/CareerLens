from typing import Literal

from pydantic import BaseModel, Field


InterviewQuestionCategory = Literal[
    "technical",
    "resume_based",
    "behavioral",
    "job_specific",
]


class InterviewCategoryScore(BaseModel):
    """Aggregated performance for one interview-question category."""

    average_overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )
    answer_count: int = Field(
        default=0,
        ge=0,
    )


class InterviewSessionReport(BaseModel):
    """On-demand deterministic report for one interview session."""

    session_id: int
    total_questions: int = Field(ge=0)
    answered_questions: int = Field(ge=0)
    average_relevance_score: float = Field(
        ge=0.0,
        le=100.0,
    )
    average_completeness_score: float = Field(
        ge=0.0,
        le=100.0,
    )
    average_technical_score: float = Field(
        ge=0.0,
        le=100.0,
    )
    overall_score: float = Field(
        ge=0.0,
        le=100.0,
    )
    category_scores: dict[
        InterviewQuestionCategory,
        InterviewCategoryScore,
    ]
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)