import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.api import skill_gap as skill_gap_api
from app.models.match_explaination import MatchEvidence
from app.models.skill_gap import SkillGapResponse
from app.services import skill_gap_service
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)


def make_explanation(
    *,
    resume_id=3,
    job_id=12,
    matched_required_skills=None,
    missing_required_skills=None,
    matched_preferred_skills=None,
    evidence=None,
):
    return type(
        "FakeMatchExplanation",
        (),
        {
            "resume_id": resume_id,
            "job_id": job_id,
            "matched_required_skills": (
                matched_required_skills or []
            ),
            "missing_required_skills": (
                missing_required_skills or []
            ),
            "matched_preferred_skills": (
                matched_preferred_skills or []
            ),
            "evidence": evidence or [],
        },
    )()


def test_all_required_skills_are_matched(monkeypatch):
    monkeypatch.setattr(
        skill_gap_service,
        "explain_match",
        lambda **kwargs: make_explanation(
            matched_required_skills=[
                "Python",
                "FastAPI",
            ],
        ),
    )

    result = skill_gap_service.get_skill_gap(
        resume_id=3,
        job_id=12,
        session=object(),
    )

    assert result.total_required_skills == 2
    assert result.matched_count == 2
    assert result.partial_count == 0
    assert result.missing_count == 0
    assert [item.skill for item in result.matched] == [
        "Python",
        "FastAPI",
    ]
    assert result.missing == []
    assert result.partial == []


def test_missing_required_skills_have_no_evidence_and_high_priority(
    monkeypatch,
):
    evidence = [
        MatchEvidence(
            skill="Python",
            source_type="skill",
            source_title="Technical skills",
            excerpt="Python",
            strength="direct",
        ),
    ]

    monkeypatch.setattr(
        skill_gap_service,
        "explain_match",
        lambda **kwargs: make_explanation(
            matched_required_skills=["Python"],
            missing_required_skills=["SQL"],
            evidence=evidence,
        ),
    )

    result = skill_gap_service.get_skill_gap(
        resume_id=3,
        job_id=12,
        session=object(),
    )

    assert result.missing_count == 1
    assert result.missing[0].skill == "SQL"
    assert result.missing[0].evidence == []
    assert result.missing[0].priority == "high"


def test_preferred_skills_never_appear_in_required_collections(
    monkeypatch,
):
    monkeypatch.setattr(
        skill_gap_service,
        "explain_match",
        lambda **kwargs: make_explanation(
            matched_required_skills=["Python"],
            missing_required_skills=["SQL"],
            matched_preferred_skills=["Docker"],
        ),
    )

    result = skill_gap_service.get_skill_gap(
        resume_id=3,
        job_id=12,
        session=object(),
    )

    all_required_items = [
        *result.matched,
        *result.partial,
        *result.missing,
    ]

    assert [item.skill for item in all_required_items] == [
        "Python",
        "SQL",
    ]
    assert "Docker" not in [
        item.skill for item in all_required_items
    ]


def test_existing_match_evidence_is_reused(monkeypatch):
    evidence = [
        MatchEvidence(
            skill="FastAPI",
            source_type="project",
            source_title="CareerLens",
            excerpt="Built APIs with FastAPI.",
            strength="supporting",
        ),
    ]

    monkeypatch.setattr(
        skill_gap_service,
        "explain_match",
        lambda **kwargs: make_explanation(
            matched_required_skills=["FastAPI"],
            evidence=evidence,
        ),
    )

    result = skill_gap_service.get_skill_gap(
        resume_id=3,
        job_id=12,
        session=object(),
    )

    assert result.matched[0].evidence == evidence


def test_evidence_is_grouped_case_insensitively_by_skill(
    monkeypatch,
):
    evidence = [
        MatchEvidence(
            skill="FastAPI",
            source_type="skill",
            source_title="Technical skills",
            excerpt="FastAPI",
            strength="direct",
        ),
        MatchEvidence(
            skill="fastapi",
            source_type="project",
            source_title="CareerLens",
            excerpt="Built APIs with FastAPI.",
            strength="supporting",
        ),
    ]

    monkeypatch.setattr(
        skill_gap_service,
        "explain_match",
        lambda **kwargs: make_explanation(
            matched_required_skills=["FASTAPI"],
            evidence=evidence,
        ),
    )

    result = skill_gap_service.get_skill_gap(
        resume_id=3,
        job_id=12,
        session=object(),
    )

    assert result.matched[0].skill == "FASTAPI"
    assert result.matched[0].evidence == evidence


def test_partial_classification_remains_conservative(monkeypatch):
    monkeypatch.setattr(
        skill_gap_service,
        "explain_match",
        lambda **kwargs: make_explanation(
            matched_required_skills=["Python"],
            missing_required_skills=["Django"],
        ),
    )

    result = skill_gap_service.get_skill_gap(
        resume_id=3,
        job_id=12,
        session=object(),
    )

    assert result.partial == []
    assert [item.skill for item in result.missing] == ["Django"]


def test_service_propagates_resume_analysis_error(monkeypatch):
    def raise_error(**kwargs):
        raise ResumeAnalysisNotFoundError(
            "analysis missing"
        )

    monkeypatch.setattr(
        skill_gap_service,
        "explain_match",
        raise_error,
    )

    with pytest.raises(ResumeAnalysisNotFoundError):
        skill_gap_service.get_skill_gap(
            resume_id=3,
            job_id=12,
            session=object(),
        )


def test_service_propagates_job_error(monkeypatch):
    def raise_error(**kwargs):
        raise JobNotFoundError("job missing")

    monkeypatch.setattr(
        skill_gap_service,
        "explain_match",
        raise_error,
    )

    with pytest.raises(JobNotFoundError):
        skill_gap_service.get_skill_gap(
            resume_id=3,
            job_id=12,
            session=object(),
        )


def test_api_returns_successful_response(monkeypatch):
    result = SkillGapResponse(
        resume_id=3,
        job_id=12,
        total_required_skills=2,
        matched_count=1,
        partial_count=0,
        missing_count=1,
        matched=[],
        partial=[],
        missing=[],
    )

    monkeypatch.setattr(
        skill_gap_api,
        "build_skill_gap",
        lambda **kwargs: result,
    )

    response = skill_gap_api.get_resume_job_skill_gap(
        resume_id=3,
        job_id=12,
        db=object(),
    )

    assert response == result


def test_api_maps_resume_analysis_error_to_404(monkeypatch):
    def raise_error(**kwargs):
        raise ResumeAnalysisNotFoundError(
            "analysis missing"
        )

    monkeypatch.setattr(
        skill_gap_api,
        "build_skill_gap",
        raise_error,
    )

    with pytest.raises(HTTPException) as error:
        skill_gap_api.get_resume_job_skill_gap(
            resume_id=3,
            job_id=12,
            db=object(),
        )

    assert error.value.status_code == 404


def test_api_maps_job_error_to_404(monkeypatch):
    def raise_error(**kwargs):
        raise JobNotFoundError("job missing")

    monkeypatch.setattr(
        skill_gap_api,
        "build_skill_gap",
        raise_error,
    )

    with pytest.raises(HTTPException) as error:
        skill_gap_api.get_resume_job_skill_gap(
            resume_id=3,
            job_id=12,
            db=object(),
        )

    assert error.value.status_code == 404


def test_api_maps_database_error_to_500(monkeypatch):
    def raise_error(**kwargs):
        raise SQLAlchemyError("database failure")

    monkeypatch.setattr(
        skill_gap_api,
        "build_skill_gap",
        raise_error,
    )

    with pytest.raises(HTTPException) as error:
        skill_gap_api.get_resume_job_skill_gap(
            resume_id=3,
            job_id=12,
            db=object(),
        )

    assert error.value.status_code == 500