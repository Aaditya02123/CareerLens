from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.interview_execution import (
    InterviewExecutionSession,
    InterviewSessionAnswer,
    InterviewSessionQuestion,
)
from app.models.interview_model_answer import DeliveryMetrics, ModelAnswerResponse
from app.services.interview_execution_service import (
    InterviewExecutionAnswerError,
    InterviewExecutionSessionNotFoundError,
)
from app.services.llm.generator import LLMGenerationProvider
from app.services.llm.ollama_generator import get_ollama_generation_provider

_LOGGER = logging.getLogger(__name__)

FILLER_PATTERN = re.compile(
    r"\b(um|uh|er|ah|like|you know|basically|actually|sort of|kind of|i mean)\b",
    re.IGNORECASE,
)


def calculate_delivery_metrics(
    text: str,
    duration_seconds: float | None = None,
) -> DeliveryMetrics:
    words = [w for w in text.split() if w.strip()]
    word_count = len(words)

    matches = [m.lower() for m in FILLER_PATTERN.findall(text)]
    filler_count = len(matches)

    if duration_seconds and duration_seconds > 5:
        wpm = int((word_count / duration_seconds) * 60)
    else:
        # Approximate standard speaking pace: 130-150 WPM
        wpm = 135 if word_count > 30 else 110

    if wpm < 110:
        pacing = "deliberate / slow"
    elif wpm > 175:
        pacing = "fast / rushed"
    else:
        pacing = "optimal (120-160 WPM)"

    # Clarity score: baseline 9.0, docked for filler concentration
    filler_ratio = filler_count / max(1, word_count)
    clarity_score = round(max(4.0, min(10.0, 9.5 - (filler_ratio * 35))), 1)

    return DeliveryMetrics(
        wpm=wpm,
        word_count=word_count,
        filler_word_count=filler_count,
        filler_words_detected=list(set(matches)),
        pacing_rating=pacing,
        clarity_score=clarity_score,
    )


def build_deterministic_model_answer(
    question_text: str,
    target_competency: str,
    assessment_objective: str,
    candidate_answer: str,
) -> tuple[str, list[str], list[str]]:
    """Synthesizes an exemplar STAR response and delta nuances deterministically."""

    model_answer = (
        f"**Situation & Task:** In a production environment addressing {target_competency.lower()}, "
        f"the primary challenge was to {assessment_objective.lower().rstrip('.')}.\n\n"
        f"**Action:** I began by analyzing the architectural constraints and edge cases. "
        f"Rather than taking a generic approach, I isolated critical state, implemented resilient error boundaries, "
        f"and validated the pipeline using automated contract tests.\n\n"
        f"**Result:** This delivered a robust, measurable improvement: operational downtime dropped, "
        f"system predictability was guaranteed, and the solution cleanly scaled under peak traffic."
    )

    missing_nuances: list[str] = []
    lower_ans = candidate_answer.lower()

    if not any(k in lower_ans for k in ["metric", "percent", "%", "latency", "scale", "performance"]):
        missing_nuances.append("Quantifiable impact: Include measurable metrics (e.g. latency, throughput, scale).")

    if not any(k in lower_ans for k in ["trade-off", "tradeoff", "alternative", "choice", "decision"]):
        missing_nuances.append("Engineering trade-offs: Explicitly state why this approach was preferred over alternatives.")

    if not any(k in lower_ans for k in ["error", "failure", "fallback", "recovery", "timeout"]):
        missing_nuances.append("Failure modes: Detail error recovery, retries, and edge-case handling.")

    if not missing_nuances:
        missing_nuances.append("Deepen architectural context: Mention system observability and monitoring hooks.")

    strengths: list[str] = []
    if len(lower_ans.split()) > 25:
        strengths.append(f"Demonstrated working conceptual familiarity with {target_competency}.")
    if any(k in lower_ans for k in ["team", "user", "customer", "business"]):
        strengths.append("Connected technical execution with user and organizational outcomes.")
    if not strengths:
        strengths.append("Directly addressed the prompt with clear foundational phrasing.")

    return model_answer, missing_nuances, strengths


class InterviewModelAnswerService:
    def __init__(
        self,
        db: Session,
        provider: LLMGenerationProvider | None = None,
    ) -> None:
        self.db = db
        self.provider = provider

    def generate_for_answer(
        self,
        session_id: int,
        answer_id: int,
        duration_seconds: float | None = None,
    ) -> ModelAnswerResponse:
        session = self.db.get(InterviewExecutionSession, session_id)
        if session is None:
            raise InterviewExecutionSessionNotFoundError(
                f"Interview session {session_id} was not found."
            )

        answer = self.db.get(InterviewSessionAnswer, answer_id)
        if answer is None or answer.session_id != session_id:
            raise InterviewExecutionAnswerError(
                f"Answer {answer_id} does not belong to session {session_id}."
            )

        question = answer.question_record
        if question is None:
            question = self.db.get(
                InterviewSessionQuestion, answer.session_question_id
            )

        delivery_metrics = calculate_delivery_metrics(
            answer.answer,
            duration_seconds=duration_seconds,
        )

        model_answer, missing_nuances, strengths = build_deterministic_model_answer(
            question_text=question.question,
            target_competency=question.target_competency,
            assessment_objective=question.assessment_objective,
            candidate_answer=answer.answer,
        )

        return ModelAnswerResponse(
            question_id=question.id,
            question_text=question.question,
            target_competency=question.target_competency,
            candidate_answer=answer.answer,
            model_answer=model_answer,
            missing_critical_nuances=missing_nuances,
            key_strengths_demonstrated=strengths,
            delivery_metrics=delivery_metrics,
        )
