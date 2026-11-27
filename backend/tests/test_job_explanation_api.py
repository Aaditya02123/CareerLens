import pytest
from fastapi import HTTPException

import app.core.init_db  # noqa: F401
from app.api import match_explaination as api_module
from app.models.job_explanation import JobExplanationResult
from app.models.user import User


def test_api_delegates_and_returns_all_fields(monkeypatch):
    result = JobExplanationResult(
        resume_id=3,
        job_id=12,
        hybrid_score=0.92,
        why_it_fits="Python is relevant.",
        gap="SQL is missing.",
        next_step="Prioritize developing SQL.",
        explanation=(
            "WHY IT FITS\nPython is relevant.\n\n"
            "GAP\nSQL is missing.\n\n"
            "NEXT STEP\nPrioritize developing SQL."
        ),
    )

    monkeypatch.setattr(
        api_module,
        "require_owned_resume",
        lambda resume_id, user, db: None,
    )
    monkeypatch.setattr(
        api_module,
        "generate_job_explanation",
        lambda **kwargs: result,
    )

    fake_user = User(
        id=1,
        email="test@careerlens.dev",
        name="Test User",
        password_hash="pw",
    )

    response = api_module.get_ai_job_explanation(
        resume_id=3,
        job_id=12,
        db=object(),
        current_user=fake_user,
    )

    assert response.why_it_fits == result.why_it_fits
    assert response.gap == result.gap
    assert response.next_step == result.next_step
    assert response.explanation == result.explanation


def test_api_preserves_auth_http_exceptions(monkeypatch):
    def fake_require_owned_resume(resume_id, user, db):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this resume.",
        )

    monkeypatch.setattr(
        api_module,
        "require_owned_resume",
        fake_require_owned_resume,
    )

    fake_user = User(
        id=2,
        email="other@careerlens.dev",
        name="Other User",
        password_hash="pw",
    )

    with pytest.raises(HTTPException) as exc_info:
        api_module.get_ai_job_explanation(
            resume_id=3,
            job_id=12,
            db=object(),
            current_user=fake_user,
        )

    assert exc_info.value.status_code == 403
    assert "permission" in exc_info.value.detail