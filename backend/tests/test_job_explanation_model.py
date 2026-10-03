from app.models.job_explanation import (
    AIJobExplanationResponse,
    JobExplanationResult,
)


def test_structured_result_and_legacy_explanation_agree():
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

    assert result.why_it_fits in result.explanation
    assert result.gap in result.explanation
    assert result.next_step in result.explanation


def test_api_response_keeps_structured_and_legacy_fields():
    response = AIJobExplanationResponse(
        resume_id=3,
        job_id=12,
        hybrid_score=0.92,
        explanation=(
            "WHY IT FITS\nPython is relevant.\n\n"
            "GAP\nSQL is missing.\n\n"
            "NEXT STEP\nPrioritize developing SQL."
        ),
        why_it_fits="Python is relevant.",
        gap="SQL is missing.",
        next_step="Prioritize developing SQL.",
    )

    assert response.why_it_fits in response.explanation
    assert response.gap in response.explanation
    assert response.next_step in response.explanation