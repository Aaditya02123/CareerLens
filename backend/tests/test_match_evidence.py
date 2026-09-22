from app.models.resume import StructuredResume
from app.services.match_explaination_service import (
    _build_skill_evidence,
    _skill_occurs_in_text,
)


def test_skill_occurs_in_text_matches_exact_skill():
    assert _skill_occurs_in_text(
        "FastAPI",
        "Built REST APIs using FastAPI.",
    )


def test_skill_occurs_in_text_does_not_match_partial_word():
    assert not _skill_occurs_in_text(
        "SQL",
        "NoSQL database experience.",
    )


def test_build_skill_evidence_finds_project_evidence():
    resume = StructuredResume(
        skills=["Python", "FastAPI"],
        projects=[
            (
                "CareerLens\n"
                "Technologies: FastAPI, PostgreSQL\n"
                "Built REST APIs using FastAPI."
            )
        ],
    )

    evidence = _build_skill_evidence(
        structured_resume=resume,
        skills=["FastAPI"],
    )

    assert len(evidence) == 2

    assert evidence[0].source_type == "skill"
    assert evidence[0].source_title == "Technical skills"
    assert evidence[0].strength == "direct"

    assert evidence[1].source_type == "project"
    assert evidence[1].source_title == "CareerLens"
    assert evidence[1].strength == "supporting"
    assert "FastAPI" in evidence[1].excerpt


def test_build_skill_evidence_ignores_unmatched_skill():
    resume = StructuredResume(
        skills=["Python"],
        projects=[
            "CareerLens\nTechnologies: FastAPI"
        ],
    )

    evidence = _build_skill_evidence(
        structured_resume=resume,
        skills=["Docker"],
    )

    assert evidence == []