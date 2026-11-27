from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DeliveryMetrics(BaseModel):
    wpm: int = Field(ge=0, description="Words per minute")
    word_count: int = Field(ge=0)
    filler_word_count: int = Field(ge=0)
    filler_words_detected: list[str] = Field(default_factory=list)
    pacing_rating: str = Field(description="slow, optimal, fast")
    clarity_score: float = Field(ge=0.0, le=10.0)


class ModelAnswerResponse(BaseModel):
    question_id: int
    question_text: str
    target_competency: str
    candidate_answer: str
    model_answer: str
    structure_framework: str = "STAR (Situation, Task, Action, Result)"
    missing_critical_nuances: list[str] = Field(default_factory=list)
    key_strengths_demonstrated: list[str] = Field(default_factory=list)
    delivery_metrics: DeliveryMetrics
