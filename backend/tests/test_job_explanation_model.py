from app.models.job_explanation import AIJobExplanationResponse


def test_ai_job_explanation_response():
    response = AIJobExplanationResponse(
        resume_id=2,
        job_id=1,
        hybrid_score=0.92,
        explanation=(
            "Your strongest alignment comes from "
            "Python and FastAPI experience."
        ),
    )

    assert response.resume_id == 2
    assert response.job_id == 1
    assert response.hybrid_score == 0.92
    assert "FastAPI" in response.explanation


def test_ai_job_explanation_requires_explanation():
    response = AIJobExplanationResponse(
        resume_id=2,
        job_id=1,
        hybrid_score=0.75,
        explanation="Grounded explanation.",
    )

    assert response.explanation == "Grounded explanation."