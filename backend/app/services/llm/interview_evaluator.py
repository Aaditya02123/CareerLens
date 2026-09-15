from __future__ import annotations

import json
from typing import Any

from app.services.llm.base import (
    InterviewEvaluationProvider,
    LLMEvaluationPayload,
)


def build_interview_evaluation_prompt(
    context: dict[str, Any],
) -> str:
    """Build the constrained evaluation prompt."""
    serialized_context = json.dumps(
        context,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
Evaluate the submitted interview answer using only the supplied context.

Return valid JSON only with exactly these fields:
- relevance_score: number from 0 to 100
- completeness_score: number from 0 to 100
- technical_score: number from 0 to 100
- overall_score: number from 0 to 100
- strengths: array of concise evidence-based strings
- improvements: array of concise actionable strings

Rules:
- Do not infer personality, honesty, emotions, mental state, or employability.
- Do not invent candidate experience or unsupported skills.
- Distinguish "not mentioned" from "incorrect".
- For technical or job-specific questions, use required skills when available.
- For resume-based questions, use only the supplied structured resume.
- For behavioral questions, evaluate textual specificity and structure only.
- If context is insufficient, score conservatively and explain why.
- Do not include Markdown fences or additional fields.

Context:
{serialized_context}
""".strip()


class InterviewEvaluator:
    """Application-level evaluator using an injected provider."""

    def __init__(self, provider: InterviewEvaluationProvider) -> None:
        self.provider = provider

    def evaluate(
        self,
        context: dict[str, Any],
    ) -> LLMEvaluationPayload:
        """Evaluate context and validate the provider result."""
        prompt = build_interview_evaluation_prompt(context)
        result = self.provider.evaluate(
            prompt=prompt,
            context=context,
        )
        return LLMEvaluationPayload.model_validate(result)