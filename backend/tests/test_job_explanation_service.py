from app.models.match_explaination import MatchEvidence
from app.services.job_explanation_service import (
    JOB_EXPLANATION_SYSTEM_PROMPT,
    build_job_explanation_prompt,
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
        MatchEvidence(
            skill="PostgreSQL",
            source_type="skill",
            source_title="Technical Skills",
            excerpt="PostgreSQL",
            strength="supporting",
        ),
    ]


def test_job_explanation_prompt_contains_job_context():
    prompt = build_job_explanation_prompt(
        job_title="Backend Developer",
        company="TechCorp",
        match_level="strong",
        hybrid_score=0.92,
        required_skill_score=1.0,
        preferred_skill_score=0.75,
        semantic_score=0.79,
        matched_required_skills=["Python", "FastAPI", "PostgreSQL"],
        missing_required_skills=[],
        matched_preferred_skills=["Docker"],
        evidence=make_evidence(),
    )

    assert "Backend Developer" in prompt
    assert "TechCorp" in prompt
    assert "Python" in prompt
    assert "FastAPI" in prompt
    assert "PostgreSQL" in prompt


def test_job_explanation_prompt_contains_resume_evidence():
    prompt = build_job_explanation_prompt(
        job_title="Backend Developer",
        company="TechCorp",
        match_level="strong",
        hybrid_score=0.92,
        required_skill_score=1.0,
        preferred_skill_score=0.75,
        semantic_score=0.79,
        matched_required_skills=["FastAPI"],
        missing_required_skills=[],
        matched_preferred_skills=[],
        evidence=make_evidence(),
    )

    assert "NagarSetu" in prompt
    assert "Built the backend using FastAPI." in prompt
    assert "direct" in prompt
    assert "supporting" in prompt


def test_job_explanation_prompt_contains_skill_gap():
    prompt = build_job_explanation_prompt(
        job_title="Backend Developer",
        company="TechCorp",
        match_level="partial",
        hybrid_score=0.68,
        required_skill_score=0.67,
        preferred_skill_score=0.5,
        semantic_score=0.71,
        matched_required_skills=["Python", "FastAPI"],
        missing_required_skills=["Docker"],
        matched_preferred_skills=[],
        evidence=make_evidence(),
    )

    assert "Docker" in prompt
    assert "missing_required" in prompt


def test_system_prompt_prevents_hallucinated_evidence():
    assert "Use only the supplied resume_evidence." in JOB_EXPLANATION_SYSTEM_PROMPT
    assert "Never invent additional resume evidence." in JOB_EXPLANATION_SYSTEM_PROMPT