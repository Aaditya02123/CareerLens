from app.models.match_explaination import MatchEvidence
from app.services import job_explanation_service as service_module
from app.services.job_explanation_service import (
    _sanitize_why_it_fits,
    build_deterministic_gap,
    build_deterministic_next_step,
    compose_job_explanation,
    generate_job_explanation,
)


def make_evidence() -> list[MatchEvidence]:
    return [
        MatchEvidence(
            skill="FastAPI",
            source_type="project",
            source_title="NagarSetu",
            excerpt="Built the backend using FastAPI.",
            strength="direct",
        ),
    ]


def test_sanitizer_removes_llm_sections():
    result = _sanitize_why_it_fits(
        "WHY IT FITS\nPython is relevant.\n\n"
        "GAP\nNo gaps.\n\n"
        "NEXT STEP\nLearn SQL."
    )

    assert result == "Python is relevant."


def test_compose_uses_already_sanitized_values():
    result = compose_job_explanation(
        why_it_fits="Python is relevant.",
        gap="SQL is a required skill that is currently missing.",
        next_step="Prioritize developing SQL.",
    )

    assert result == (
        "WHY IT FITS\nPython is relevant.\n\n"
        "GAP\nSQL is a required skill that is currently missing.\n\n"
        "NEXT STEP\nPrioritize developing SQL."
    )


class FakeJob:
    title = "Backend Developer"
    company = "TechCorp"


class FakeJobRepository:
    def __init__(self, session) -> None:
        self.session = session

    def get_by_id(self, job_id: int):
        return FakeJob()


class FakeProvider:
    def generate(self, *, system_prompt: str, prompt: str) -> str:
        return (
            "WHY IT FITS\nPython is relevant.\n\n"
            "GAP\nNo gaps.\n\n"
            "NEXT STEP\nLearn SQL."
        )


class FakeGenerator:
    def __init__(self, provider) -> None:
        self.provider = provider

    def generate(self, **kwargs) -> str:
        return self.provider.generate(
            system_prompt="ignored",
            prompt="ignored",
        )


def test_orchestration_cannot_override_deterministic_sections(
    monkeypatch,
):
    deterministic = type(
        "DeterministicExplanation",
        (),
        {
            "resume_id": 3,
            "job_id": 12,
            "match_level":"strong",
            "hybrid_score": 0.92,
            "required_skill_score": 0.9,
            "preferred_skill_score": 0.8,
            "semantic_score": 0.9,
            "missing_required_skills": ["SQL"],
            "matched_required_skills": ["Python"],
            "matched_preferred_skills": [],
            "evidence": make_evidence(),
        },
    )()

    monkeypatch.setattr(
        service_module,
        "JobRepository",
        FakeJobRepository,
    )
    monkeypatch.setattr(
        service_module,
        "explain_match",
        lambda **kwargs: deterministic,
    )

    import app.services.job_explanation_generator as generator_module

    monkeypatch.setattr(
        generator_module,
        "JobExplanationGenerator",
        FakeGenerator,
    )

    result = generate_job_explanation(
        resume_id=3,
        job_id=12,
        session=object(),
        provider=FakeProvider(),
    )

    assert result.why_it_fits == "Python is relevant."
    assert result.gap == (
        "SQL is a required skill that is currently "
        "missing from the resume analysis."
    )
    assert result.next_step == (
        "Prioritize developing SQL because it is the "
        "remaining required-skill gap."
    )
    assert "No gaps." not in result.gap
    assert "Learn SQL." not in result.next_step

    assert result.why_it_fits in result.explanation
    assert result.gap in result.explanation
    assert result.next_step in result.explanation