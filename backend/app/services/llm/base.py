from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class LLMEvaluationPayload(BaseModel):
    """Validated structured result returned by an LLM provider."""

    relevance_score: float = Field(ge=0.0, le=100.0)
    completeness_score: float = Field(ge=0.0, le=100.0)
    technical_score: float = Field(ge=0.0, le=100.0)
    overall_score: float = Field(ge=0.0, le=100.0)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class InterviewEvaluationProvider(Protocol):
    """Provider abstraction for structured interview evaluation."""

    def evaluate(
        self,
        prompt: str,
        context: dict[str, Any],
    ) -> LLMEvaluationPayload:
        ...