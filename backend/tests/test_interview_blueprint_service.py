import json
import logging
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.interview_blueprint import InterviewBlueprintConfig
from app.services import interview_blueprint_service as service_module
from app.services.interview_blueprint_service import (
    BlueprintJobDescriptionError,
    BlueprintJobNotFoundError,
    BlueprintResumeAnalysisNotFoundError,
    BlueprintResumeNotFoundError,
    InterviewBlueprintProviderError,
    generate_interview_blueprint,
)
from app.services.llm.ollama_generator import OllamaProviderUnavailableError
from app.services.llm.observability import GenerationFailureCategory


def _provider_payload(config: InterviewBlueprintConfig) -> str:
    return json.dumps(
        {
            "target_role": "Backend Engineer",
            "interview_type": config.interview_type,
            "difficulty": config.difficulty,
            "duration_minutes": config.duration_minutes,
            "question_count": config.question_count,
            "competencies": [
                {
                    "name": "Python",
                    "description": "Python implementation",
                    "category": "technical",
                    "weight_percent": 100,
                    "related_job_requirements": ["Python"],
                    "related_resume_evidence": ["Python"],
                    "assessment_objectives": ["Explain implementation choices"],
                }
            ],
            "questions": [
                {
                    "question_id": f"q-{index}",
                    "question": "How would you use Python here?",
                    "category": "technical",
                    "difficulty": "medium",
                    "target_competency": "Python",
                    "assessment_objective": "Assess Python reasoning",
                    "relevance_reason": "Python is required by the job.",
                    "supporting_job_requirement": "Python",
                    "supporting_resume_evidence": "Python",
                    "expected_answer_topics": ["trade-offs"],
                    "rubric_criteria": ["correctness"],
                    "estimated_response_seconds": 60,
                    "follow_up_allowed": True,
                }
                for index in range(config.question_count)
            ],
            "rubric": [
                {
                    "criterion_id": "correctness",
                    "name": "Technical correctness",
                    "category": "technical",
                    "description": "The answer is technically sound.",
                    "weight_percent": 100,
                    "scoring_guidance": ["0: no evidence", "5: excellent"],
                    "evidence_expectations": ["Explain the approach"],
                }
            ],
        }
    )


class FakeProvider:
    def __init__(self, response: str):
        self.response = response

    def generate(self, system_prompt: str, prompt: str) -> str:
        return self.response


class SequenceProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def generate(self, system_prompt: str, prompt: str) -> str:
        self.calls += 1
        return self.responses.pop(0)


class UnavailableProvider:
    def __init__(self):
        self.calls = 0

    def generate(self, system_prompt: str, prompt: str) -> str:
        self.calls += 1
        raise OllamaProviderUnavailableError("Ollama is unavailable.")


class FakeRepository:
    def __init__(self):
        self.created = None

    def create(self, **kwargs):
        self.created = kwargs
        return SimpleNamespace(
            id=7,
            resume_id=1,
            job_id=2,
            target_role=kwargs["target_role"],
            interview_type=kwargs["interview_type"],
            difficulty=kwargs["difficulty"],
            duration_minutes=kwargs["duration_minutes"],
            question_count=kwargs["question_count"],
            created_at=datetime.now(timezone.utc),
            competencies=[],
            questions=[],
            rubric=[],
        )


@pytest.fixture
def context(monkeypatch):
    config = InterviewBlueprintConfig(question_count=2)
    resume = SimpleNamespace(id=1)
    job = SimpleNamespace(
        id=2,
        title="Backend Engineer",
        description="Build Python services.",
        responsibilities=["Build Python services"],
        required_skills=["Python"],
        preferred_skills=[],
    )
    analysis = SimpleNamespace(
        resume_id=1,
        structured_resume={"skills": ["Python"]},
        categorized_skills={
            "skills": [{"name": "Python", "category": "Programming Language"}]
        },
    )
    repository = FakeRepository()

    class FakeResumeRepository:
        def __init__(self, session):
            pass

        def get_by_id(self, value):
            return resume if value == 1 else None

    class FakeJobRepository(FakeResumeRepository):
        def get_by_id(self, value):
            return job if value == 2 else None

    class FakeAnalysisRepository(FakeResumeRepository):
        def get_by_resume_id(self, value):
            return analysis if value == 1 else None

    monkeypatch.setattr(service_module, "ResumeRepository", FakeResumeRepository)
    monkeypatch.setattr(service_module, "JobRepository", FakeJobRepository)
    monkeypatch.setattr(
        service_module,
        "ResumeAnalysisRepository",
        FakeAnalysisRepository,
    )
    monkeypatch.setattr(
        service_module,
        "InterviewBlueprintRepository",
        lambda session: repository,
    )
    return config, repository


def test_generation_validates_provider_output_and_persists(context):
    config, repository = context
    result = generate_interview_blueprint(
        resume_id=1,
        job_id=2,
        session=object(),
        config=config,
        provider=FakeProvider(_provider_payload(config)),
    )

    assert result.id == 7
    assert repository.created["question_count"] == 2
    assert len(repository.created["questions"]) == 2


def test_generation_logs_safe_stage_timings(context, caplog):
    config, _ = context
    caplog.set_level(logging.INFO, logger="app.llm")

    generate_interview_blueprint(
        resume_id=1,
        job_id=2,
        session=object(),
        config=config,
        provider=FakeProvider(_provider_payload(config)),
    )

    events = [json.loads(record.message) for record in caplog.records]
    success = next(
        event
        for event in events
        if event["event"] == "llm_generation" and event["success"]
    )
    assert success["operation"] == "blueprint"
    assert success["provider_name"] == "FakeProvider"
    assert success["attempt"] == 1
    assert success["json_parse_ms"] >= 0
    assert success["pydantic_validation_ms"] >= 0
    assert success["grounding_validation_ms"] >= 0
    assert success["total_operation_ms"] >= 0
    assert "Build Python services." not in caplog.text


def test_retry_logs_failure_category_and_exhaustion(context, caplog):
    config, _ = context
    caplog.set_level(logging.INFO, logger="app.llm")

    with pytest.raises(InterviewBlueprintProviderError):
        generate_interview_blueprint(
            resume_id=1,
            job_id=2,
            session=object(),
            config=config,
            provider=SequenceProvider(["not json", "still not json"]),
        )

    events = [json.loads(record.message) for record in caplog.records]
    retry = next(
        event for event in events if event["event"] == "llm_generation_retry"
    )
    final = next(
        event
        for event in events
        if event["event"] == "llm_generation" and not event["success"]
    )
    assert retry["failure_category"] == GenerationFailureCategory.MALFORMED_JSON
    assert final["failure_category"] == GenerationFailureCategory.GENERATION_RETRY_EXHAUSTED
    assert final["root_failure_category"] == GenerationFailureCategory.MALFORMED_JSON


def test_provider_must_ground_resume_evidence(context):
    config, _ = context
    payload = json.loads(_provider_payload(config))
    payload["questions"][0]["supporting_resume_evidence"] = "Unstated skill"

    with pytest.raises(InterviewBlueprintProviderError):
        generate_interview_blueprint(
            resume_id=1,
            job_id=2,
            session=object(),
            config=config,
            provider=FakeProvider(json.dumps(payload)),
        )


@pytest.mark.parametrize(
    "interview_type",
    ["technical", "behavioral", "project_based", "mixed"],
)
def test_supported_interview_types_are_preserved(context, interview_type):
    _, repository = context
    config = InterviewBlueprintConfig(
        interview_type=interview_type,
        question_count=2,
    )
    result = generate_interview_blueprint(
        resume_id=1,
        job_id=2,
        session=object(),
        config=config,
        provider=FakeProvider(_provider_payload(config)),
    )
    assert result.interview_type == interview_type
    assert repository.created["duration_minutes"] == 30


def test_missing_resume_is_a_domain_error(monkeypatch):
    class EmptyRepository:
        def __init__(self, session):
            pass

        def get_by_id(self, value):
            return None

    monkeypatch.setattr(service_module, "ResumeRepository", EmptyRepository)
    with pytest.raises(BlueprintResumeNotFoundError):
        generate_interview_blueprint(
            resume_id=1,
            job_id=2,
            session=object(),
            provider=FakeProvider("{}"),
        )


def test_malformed_provider_response_is_rejected(context):
    config, _ = context
    with pytest.raises(InterviewBlueprintProviderError):
        generate_interview_blueprint(
            resume_id=1,
            job_id=2,
            session=object(),
            config=config,
            provider=FakeProvider("not json"),
        )


def test_malformed_provider_response_is_retried_once(context):
    config, repository = context
    provider = SequenceProvider(["not json", _provider_payload(config)])

    result = generate_interview_blueprint(
        resume_id=1,
        job_id=2,
        session=object(),
        config=config,
        provider=provider,
    )

    assert result.id == 7
    assert provider.calls == 2
    assert repository.created is not None


def test_malformed_provider_response_is_not_retried_more_than_once(context):
    config, repository = context
    provider = SequenceProvider(["not json", "still not json"])

    with pytest.raises(InterviewBlueprintProviderError):
        generate_interview_blueprint(
            resume_id=1,
            job_id=2,
            session=object(),
            config=config,
            provider=provider,
        )

    assert provider.calls == 2
    assert repository.created is None


def test_provider_unavailable_is_not_retried(context):
    config, repository = context
    provider = UnavailableProvider()

    with pytest.raises(OllamaProviderUnavailableError):
        generate_interview_blueprint(
            resume_id=1,
            job_id=2,
            session=object(),
            config=config,
            provider=provider,
        )

    assert provider.calls == 1
    assert repository.created is None


def test_missing_job_and_analysis_are_rejected(context, monkeypatch):
    config, _ = context

    class MissingJobRepository:
        def __init__(self, session):
            pass

        def get_by_id(self, value):
            return None

    monkeypatch.setattr(service_module, "JobRepository", MissingJobRepository)
    with pytest.raises(BlueprintJobNotFoundError):
        generate_interview_blueprint(
            resume_id=1,
            job_id=2,
            session=object(),
            config=config,
            provider=FakeProvider("{}"),
        )

    class MissingAnalysisRepository:
        def __init__(self, session):
            pass

        def get_by_resume_id(self, value):
            return None

    monkeypatch.setattr(
        service_module,
        "ResumeAnalysisRepository",
        MissingAnalysisRepository,
    )
    class PresentJobRepository:
        def __init__(self, session):
            pass

        def get_by_id(self, value):
            return SimpleNamespace(
                id=2,
                title="Backend Engineer",
                description="Build Python services.",
                responsibilities=["Build Python services"],
                required_skills=["Python"],
                preferred_skills=[],
            )

    monkeypatch.setattr(service_module, "JobRepository", PresentJobRepository)
    with pytest.raises(BlueprintResumeAnalysisNotFoundError):
        generate_interview_blueprint(
            resume_id=1,
            job_id=2,
            session=object(),
            config=config,
            provider=FakeProvider("{}"),
        )


def test_empty_job_description_is_rejected(context, monkeypatch):
    config, _ = context
    original = service_module.JobRepository

    class EmptyDescriptionRepository:
        def __init__(self, session):
            self.repository = original(session)

        def get_by_id(self, value):
            job = self.repository.get_by_id(value)
            return SimpleNamespace(
                id=job.id,
                title=job.title,
                description="",
                responsibilities=job.responsibilities,
                required_skills=job.required_skills,
                preferred_skills=job.preferred_skills,
            )

    monkeypatch.setattr(service_module, "JobRepository", EmptyDescriptionRepository)
    with pytest.raises(BlueprintJobDescriptionError):
        generate_interview_blueprint(
            resume_id=1,
            job_id=2,
            session=object(),
            config=config,
            provider=FakeProvider("{}"),
        )
