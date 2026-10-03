from app.api import match_explaination as api_module
from app.models.job_explanation import JobExplanationResult


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
        "generate_job_explanation",
        lambda **kwargs: result,
    )

    response = api_module.get_ai_job_explanation(
        resume_id=3,
        job_id=12,
        db=object(),
    )

    assert response.why_it_fits == result.why_it_fits
    assert response.gap == result.gap
    assert response.next_step == result.next_step
    assert response.explanation == result.explanation