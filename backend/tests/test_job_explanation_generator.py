from app.models.match_explaination import (
    MatchExplanationResponse,
    MatchEvidence,
)
from app.services.job_explanation_generator import (
    JobExplanationGenerator,
)
from app.services.job_explanation_service import (
    JOB_EXPLANATION_SYSTEM_PROMPT,
)


class FakeGenerationProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.system_prompt = None
        self.prompt = None
        self.call_count = 0

    def generate(
        self,
        system_prompt: str,
        prompt: str,
    ) -> str:
        self.call_count += 1
        self.system_prompt = system_prompt
        self.prompt = prompt

        return self.response


def make_explanation() -> MatchExplanationResponse:
    return MatchExplanationResponse(
        resume_id=2,
        job_id=1,
        hybrid_score=0.92,
        required_skill_score=1.0,
        preferred_skill_score=0.75,
        semantic_score=0.79,
        matched_required_skills=[
            "Python",
            "FastAPI",
        ],
        missing_required_skills=[],
        matched_preferred_skills=[
            "Docker",
        ],
        match_level="strong",
        skill_gap_count=0,
        primary_factors=[
            "All required skills matched",
            "Strong semantic similarity",
        ],
        evidence=[
            MatchEvidence(
                skill="FastAPI",
                source_type="project",
                source_title="NagarSetu",
                excerpt="Built the backend using FastAPI.",
                strength="direct",
            ),
        ],
    )


def test_generator_calls_provider_for_why_it_fits():
    provider = FakeGenerationProvider(
        response="Python and FastAPI are supported by project evidence."
    )

    generator = JobExplanationGenerator(provider)

    result = generator.generate(
        explanation=make_explanation(),
        job_title="Backend Developer",
        company="TechCorp",
    )

    assert result == provider.response
    assert provider.call_count == 1


def test_generator_passes_grounded_context_to_provider():
    provider = FakeGenerationProvider(
        response="Grounded explanation."
    )

    generator = JobExplanationGenerator(provider)

    generator.generate(
        explanation=make_explanation(),
        job_title="Backend Developer",
        company="TechCorp",
    )

    assert provider.system_prompt == JOB_EXPLANATION_SYSTEM_PROMPT
    assert provider.prompt is not None
    assert "Backend Developer" in provider.prompt
    assert "TechCorp" in provider.prompt
    assert "Python" in provider.prompt
    assert "FastAPI" in provider.prompt
    assert "NagarSetu" in provider.prompt
    assert "Built the backend using FastAPI." in provider.prompt
    assert "GAP" not in provider.prompt
    assert "NEXT STEP" not in provider.prompt


def test_generator_strips_provider_output():
    provider = FakeGenerationProvider(
        response="  Grounded explanation.  \n"
    )

    generator = JobExplanationGenerator(provider)

    result = generator.generate(
        explanation=make_explanation(),
        job_title="Backend Developer",
        company="TechCorp",
    )

    assert result == "Grounded explanation."