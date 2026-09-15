import os

import pytest

from app.services.llm.base import LLMEvaluationPayload
from app.services.llm.providers import (
    OpenAICompatibleInterviewProvider,
)


def test_openai_compatible_llm_provider_opt_in():
    if os.getenv("RUN_LLM_INTEGRATION") != "1":
        pytest.skip(
            "LLM integration test is opt-in. "
            "Set RUN_LLM_INTEGRATION=1 to enable it."
        )

    if not os.getenv("LLM_API_KEY"):
        pytest.skip(
            "LLM_API_KEY is not configured; skipping real provider test."
        )

    context = {
        "question": "How would you use FastAPI in a backend role?",
        "answer": (
            "I would use FastAPI to build REST APIs with Python, "
            "validate request data, and organize endpoints for backend "
            "services."
        ),
        "question_category": "technical",
        "job": {
            "title": "Backend Engineer",
            "description": (
                "Build reliable backend services using Python."
            ),
            "required_skills": ["Python", "FastAPI"],
        },
        "structured_resume": {
            "name": "Integration Test Candidate",
            "email": "integration@example.com",
            "skills": ["Python", "FastAPI"],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
        },
    }

    provider = OpenAICompatibleInterviewProvider(
        timeout_seconds=30.0,
    )

    result = provider.evaluate(
        prompt=(
            "Evaluate the supplied interview answer. "
            "Return the required structured JSON response."
        ),
        context=context,
    )

    assert isinstance(result, LLMEvaluationPayload)

    assert 0.0 <= result.relevance_score <= 100.0
    assert 0.0 <= result.completeness_score <= 100.0
    assert 0.0 <= result.technical_score <= 100.0
    assert 0.0 <= result.overall_score <= 100.0

    assert isinstance(result.strengths, list)
    assert isinstance(result.improvements, list)