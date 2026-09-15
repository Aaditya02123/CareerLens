from typing import Literal

from pydantic import BaseModel, Field


class InterviewQuestion(BaseModel):
    """A deterministic interview question."""

    question: str
    category: Literal[
        "technical",
        "resume_based",
        "behavioral",
        "job_specific",
    ]
    difficulty: Literal["easy", "medium", "hard"]


class InterviewPreparationResponse(BaseModel):
    """Interview preparation questions for a resume and job."""

    resume_id: int
    job_id: int
    questions: list[InterviewQuestion] = Field(
        default_factory=list
    )