from typing import Literal

from pydantic import BaseModel, Field


class InterviewQuestion(BaseModel):
    """A deterministic interview question with explanatory metadata."""

    question: str
    category: Literal[
        "technical",
        "resume_based",
        "behavioral",
        "job_specific",
    ]
    difficulty: Literal["easy", "medium", "hard"]
    priority: Literal["high", "medium", "low"]
    reason: str


class InterviewPreparationResponse(BaseModel):
    """Interview preparation questions for a resume and job."""

    resume_id: int
    job_id: int
    questions: list[InterviewQuestion] = Field(
        default_factory=list
    )