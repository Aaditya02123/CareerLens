from __future__ import annotations

from app.models.match_explaination import MatchExplanationResponse
from app.services.job_explanation_service import (
    JOB_EXPLANATION_SYSTEM_PROMPT,
    build_job_explanation_prompt,
)
from app.services.llm.generator import LLMGenerationProvider


class JobExplanationGenerator:
    """Generate only the grounded WHY IT FITS text."""

    def __init__(self, provider: LLMGenerationProvider) -> None:
        self.provider = provider

    def generate(
        self,
        *,
        explanation: MatchExplanationResponse,
        job_title: str,
        company: str | None,
    ) -> str:
        prompt = build_job_explanation_prompt(
            job_title=job_title,
            company=company,
            match_level=explanation.match_level,
            hybrid_score=explanation.hybrid_score,
            required_skill_score=explanation.required_skill_score,
            preferred_skill_score=explanation.preferred_skill_score,
            semantic_score=explanation.semantic_score,
            matched_required_skills=explanation.matched_required_skills,
            missing_required_skills=explanation.missing_required_skills,
            matched_preferred_skills=explanation.matched_preferred_skills,
            evidence=explanation.evidence,
        )

        result = self.provider.generate(
            system_prompt=JOB_EXPLANATION_SYSTEM_PROMPT,
            prompt=prompt,
        )

        return result.strip()