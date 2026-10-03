from app.models.match_explaination import MatchEvidence
from app.services.job_explanation_service import (
    JOB_EXPLANATION_SYSTEM_PROMPT,
    _sanitize_why_it_fits,
    build_deterministic_gap,
    build_deterministic_next_step,
    build_job_explanation_prompt,
    compose_job_explanation,
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


def build_prompt(
    *,
    missing_required_skills: list[str],
) -> str:
    return build_job_explanation_prompt(
        job_title="Backend Developer",
        company="TechCorp",
        match_level="partial"
        if missing_required_skills
        else "strong",
        hybrid_score=0.68
        if missing_required_skills
        else 0.92,
        required_skill_score=0.67
        if missing_required_skills
        else 1.0,
        preferred_skill_score=0.5,
        semantic_score=0.79,
        matched_required_skills=["Python", "FastAPI"],
        missing_required_skills=missing_required_skills,
        matched_preferred_skills=["Docker"],
        evidence=make_evidence(),
    )


def test_prompt_contains_matched_skills_and_evidence():
    prompt = build_prompt(
        missing_required_skills=[]
    )

    assert "Backend Developer" in prompt
    assert "TechCorp" in prompt
    assert "Python" in prompt
    assert "FastAPI" in prompt
    assert "NagarSetu" in prompt
    assert "Built the backend using FastAPI." in prompt


def test_prompt_asks_only_for_why_it_fits():
    prompt = build_prompt(
        missing_required_skills=[]
    )

    assert "WHY IT FITS" in prompt
    assert "one or two concise plain-text sentences" in prompt
    assert "additional sections" in prompt
    assert "GAP" not in prompt
    assert "NEXT STEP" not in prompt

def test_sanitize_why_it_fits_removes_other_sections():
    result = _sanitize_why_it_fits(
        "WHY IT FITS\n"
        "Python is supported by the candidate's project evidence.\n\n"
        "GAP\n"
        "SQL is missing.\n\n"
        "NEXT STEP\n"
        "Prioritize SQL."
    )

    assert result == (
        "Python is supported by the candidate's project evidence."
    )


def test_sanitize_why_it_fits_preserves_plain_text():
    content = (
        "Python and FastAPI are supported by the candidate's "
        "project experience."
    )

    assert _sanitize_why_it_fits(content) == content

def test_system_prompt_is_grounded():
    required_rules = [
        "Never invent skills, resume evidence, qualifications, or experience.",
        "Use only supplied resume evidence",
        "Never use the job title, company, location, or other job metadata as evidence",
        "Preserve supplied evidence source_type, source_title, excerpt, and strength.",
        "Never describe supporting evidence as direct evidence.",
        "Never reinterpret scores",
        "Never change matched/missing skill status.",
        "Do not make hiring, employability, success, or selection predictions.",
        "Do not recommend external courses, websites, certifications, products,",
        "Return only the WHY IT FITS content",
        "without a heading",
        "Plain text only.",
        "Do not use Markdown.",
    ]

    for rule in required_rules:
        assert rule in JOB_EXPLANATION_SYSTEM_PROMPT


def test_deterministic_gap_without_missing_skills():
    assert (
        build_deterministic_gap([])
        == "No required skill gaps were detected."
    )


def test_deterministic_gap_with_one_missing_skill():
    result = build_deterministic_gap(["SQL"])

    assert "SQL" in result
    assert "required skill" in result
    assert "missing" in result


def test_deterministic_gap_with_multiple_missing_skills():
    result = build_deterministic_gap(
        ["SQL", "Docker", "Redis"]
    )

    assert "SQL" in result
    assert "Docker" in result
    assert "Redis" in result


def test_next_step_addresses_missing_required_skill():
    result = build_deterministic_next_step(
        missing_required_skills=["SQL"],
        matched_required_skills=["Python"],
        evidence=make_evidence(),
    )

    assert "SQL" in result
    assert "Python" not in result


def test_next_step_without_gaps_uses_existing_evidence():
    result = build_deterministic_next_step(
        missing_required_skills=[],
        matched_required_skills=["Python", "FastAPI"],
        evidence=make_evidence(),
    )

    assert "demonstrating" in result.lower()
    assert "existing" in result.lower()
    assert "evidence" in result.lower()
    assert "weakness" not in result.lower()


def test_composer_always_uses_deterministic_sections():
    result = compose_job_explanation(
        why_it_fits="Python is supported by project evidence.",
        missing_required_skills=["SQL"],
        matched_required_skills=["Python"],
        evidence=make_evidence(),
    )

    assert result.startswith(
        "WHY IT FITS\nPython is supported by project evidence."
    )
    assert "GAP\n" in result
    assert "NEXT STEP\n" in result
    assert "SQL" in result


def test_composer_ignores_llm_gap_and_next_step_sections():
    result = compose_job_explanation(
        why_it_fits=(
            "WHY IT FITS\nPython is relevant.\n\n"
            "GAP\nNo gaps.\n\n"
            "NEXT STEP\nLearn SQL."
        ),
        missing_required_skills=["Docker"],
        matched_required_skills=["Python"],
        evidence=make_evidence(),
    )

    assert "WHY IT FITS\nPython is relevant." in result
    assert "No gaps." not in result
    assert "Learn SQL." not in result
    assert result.count("WHY IT FITS") == 1
    assert result.count("GAP") == 1
    assert result.count("NEXT STEP") == 1

def test_sanitize_why_it_fits_removes_other_sections():
    result = _sanitize_why_it_fits(
        "WHY IT FITS\n"
        "Python is supported by the candidate's project evidence.\n\n"
        "GAP\n"
        "SQL is missing.\n\n"
        "NEXT STEP\n"
        "Prioritize SQL."
    )

    assert result == (
        "Python is supported by the candidate's project evidence."
    )


def test_sanitize_why_it_fits_preserves_plain_text():
    content = (
        "Python and FastAPI are supported by the candidate's "
        "project experience."
    )

    assert _sanitize_why_it_fits(content) == content