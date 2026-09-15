import pytest
from pydantic import ValidationError

from app.services.llm.base import LLMEvaluationPayload
from app.services.llm.interview_evaluator import (
    InterviewEvaluator,
    build_interview_evaluation_prompt,
)
from app.services.llm.providers import (
    LLMConfigurationError,
    OpenAICompatibleInterviewProvider,
)


@pytest.fixture
def evaluation_context():
    return {
        "question": "How would you use FastAPI in this role?",
        "answer": "I would use FastAPI to build a REST API.",
        "question_category": "technical",
        "job": {
            "title": "Backend Engineer",
            "description": "Build reliable backend services.",
            "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        },
        "structured_resume": {
            "name": "Test User",
            "email": "test@example.com",
            "skills": ["Python", "FastAPI"],
            "education": [],
            "experience": [],
            "projects": ["Career platform"],
            "certifications": [],
        },
    }


def test_prompt_contains_context_and_safety_constraints(
    evaluation_context,
):
    prompt = build_interview_evaluation_prompt(evaluation_context)

    assert evaluation_context["question"] in prompt
    assert evaluation_context["answer"] in prompt
    assert evaluation_context["question_category"] in prompt
    assert evaluation_context["job"]["title"] in prompt
    assert "Python" in prompt
    assert "FastAPI" in prompt
    assert "PostgreSQL" in prompt
    assert "Test User" in prompt
    assert "Career platform" in prompt

    assert "Return valid JSON only" in prompt
    assert "Do not infer personality" in prompt
    assert "Do not invent candidate experience" in prompt
    assert "Distinguish" in prompt
    assert "score conservatively" in prompt


class FakeProvider:
    def __init__(self, result):
        self.result = result
        self.prompt = None
        self.context = None
        self.call_count = 0

    def evaluate(self, prompt, context):
        self.call_count += 1
        self.prompt = prompt
        self.context = context
        return self.result


def test_interview_evaluator_calls_provider_with_prompt_and_context(
    evaluation_context,
):
    provider = FakeProvider(
        LLMEvaluationPayload(
            relevance_score=80.0,
            completeness_score=70.0,
            technical_score=90.0,
            overall_score=82.5,
            strengths=["The answer is relevant."],
            improvements=["Add more detail."],
        )
    )
    evaluator = InterviewEvaluator(provider)

    result = evaluator.evaluate(evaluation_context)

    assert provider.call_count == 1
    assert provider.prompt is not None
    assert evaluation_context["question"] in provider.prompt
    assert provider.context is evaluation_context
    assert isinstance(result, LLMEvaluationPayload)
    assert result.relevance_score == 80.0
    assert result.overall_score == 82.5


def test_interview_evaluator_validates_provider_scores(
    evaluation_context,
):
    provider = FakeProvider(
        {
            "relevance_score": 101.0,
            "completeness_score": 50.0,
            "technical_score": 50.0,
            "overall_score": 50.0,
            "strengths": [],
            "improvements": [],
        }
    )
    evaluator = InterviewEvaluator(provider)

    with pytest.raises(ValidationError):
        evaluator.evaluate(evaluation_context)


def test_interview_evaluator_rejects_malformed_provider_result(
    evaluation_context,
):
    provider = FakeProvider(
        {
            "relevance_score": 80.0,
            "completeness_score": 70.0,
        }
    )
    evaluator = InterviewEvaluator(provider)

    with pytest.raises(ValidationError):
        evaluator.evaluate(evaluation_context)


def test_interview_evaluator_works_with_fake_provider_only(
    evaluation_context,
):
    provider = FakeProvider(
        {
            "relevance_score": 75.0,
            "completeness_score": 65.0,
            "technical_score": 85.0,
            "overall_score": 76.5,
            "strengths": ["Relevant technical content."],
            "improvements": ["Explain the trade-offs."],
        }
    )

    result = InterviewEvaluator(provider).evaluate(evaluation_context)

    assert result.model_dump() == {
        "relevance_score": 75.0,
        "completeness_score": 65.0,
        "technical_score": 85.0,
        "overall_score": 76.5,
        "strengths": ["Relevant technical content."],
        "improvements": ["Explain the trade-offs."],
    }


def test_openai_compatible_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    provider = OpenAICompatibleInterviewProvider()

    with pytest.raises(LLMConfigurationError):
        provider.evaluate(
            prompt="Evaluate this answer.",
            context={},
        )