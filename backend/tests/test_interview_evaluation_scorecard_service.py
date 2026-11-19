from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services import interview_evaluation_scorecard_service as service_module
from app.services.interview_evaluation_scorecard_service import (
    InterviewAnswerNotFoundForEvaluationError,
    InterviewEvaluationError,
    InterviewEvaluationProviderError,
    InterviewEvaluationScorecardService,
)
from app.services.interview_execution_service import (
    InterviewExecutionSessionNotFoundError,
)
from app.services.llm.ollama_generator import OllamaProviderUnavailableError


def _criterion(criterion_id, name, weight):
    return SimpleNamespace(
        criterion_id=criterion_id,
        name=name,
        description=f"Assess {name}",
        weight_percent=weight,
        scale_min=0,
        scale_max=5,
    )


def _context():
    question = SimpleNamespace(
        id=11,
        blueprint_question_id=21,
        question="Explain how you would design a Python API.",
        question_category="technical",
        difficulty="medium",
        target_competency="Backend design",
        assessment_objective="Assess API design reasoning.",
        relevance_reason="The role requires backend design.",
        rubric_criteria=["correctness", "depth"],
        is_follow_up=False,
        parent_question_id=None,
    )
    answer = SimpleNamespace(
        id=101,
        session_id=7,
        session_question_id=11,
        answer="I would use Python and validate request data before persistence.",
    )
    record = SimpleNamespace(
        id=7,
        blueprint_id=4,
        questions=[question],
        answers=[answer],
    )
    blueprint_question = SimpleNamespace(
        id=21,
        rubric_criteria=["correctness", "depth"],
    )
    blueprint = SimpleNamespace(
        id=4,
        resume_id=3,
        job_id=9,
        questions=[blueprint_question],
        competencies=[
            SimpleNamespace(
                name="Backend design",
                description="Design reliable backend services.",
                weight_percent=100,
            )
        ],
        rubric=[
            _criterion("correctness", "Technical correctness", 60),
            _criterion("depth", "Depth of explanation", 40),
        ],
    )
    analysis = SimpleNamespace(
        structured_resume={"skills": ["Python"]},
        categorized_skills={
            "skills": [
                {"name": "Python", "category": "Programming Language"}
            ]
        },
    )
    job = SimpleNamespace(
        title="Backend Engineer",
        description="Build Python services.",
        required_skills=["Python"],
        preferred_skills=[],
    )
    return record, blueprint, analysis, job


def _provider_payload(*, answer_id=101, question_id=11, scores=(4, 2)):
    return (
        '{'
        f'"answer_id":{answer_id},'
        f'"question_id":{question_id},'
        '"competency_reference":"Backend design",'
        '"criterion_evaluations":['
        '{"criterion_id":"correctness","criterion_name":"Technical correctness",'
        f'"score":{scores[0]},"explanation":"The answer validates input.",'
        '"evidence_excerpts":["validate request data"],'
        '"improvement_suggestion":"Explain the validation boundary."},'
        '{"criterion_id":"depth","criterion_name":"Depth of explanation",'
        f'"score":{scores[1]},"explanation":"The answer is concise.",'
        '"evidence_excerpts":["before persistence"],'
        '"improvement_suggestion":"Add a concrete trade-off."}'
        '],"strengths":["Clear validation step"],'
        '"improvement_areas":["Add trade-offs"],'
        '"actionable_feedback":["Describe one failure case."],'
        '"evaluation_status":"complete"}'
    )


class FakeProvider:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def generate(self, system_prompt, prompt):
        self.calls += 1
        self.prompt = prompt
        return self.response


class SequenceProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def generate(self, system_prompt, prompt):
        self.calls += 1
        return self.responses.pop(0)


class UnavailableProvider:
    def __init__(self):
        self.calls = 0

    def generate(self, system_prompt, prompt):
        self.calls += 1
        raise OllamaProviderUnavailableError("Ollama is unavailable.")


class FakeEvaluationRepository:
    def __init__(self):
        self.evaluations = []
        self.next_id = 1

    def get_by_answer_id(self, session_id, answer_id):
        return next(
            (
                item
                for item in self.evaluations
                if item.session_id == session_id and item.answer_id == answer_id
            ),
            None,
        )

    def list_by_session_id(self, session_id):
        return [item for item in self.evaluations if item.session_id == session_id]

    def persist_evaluation(self, **kwargs):
        existing = self.get_by_answer_id(kwargs["session_id"], kwargs["answer_id"])
        if existing is not None:
            return existing
        now = datetime.now(timezone.utc)
        evaluation = SimpleNamespace(
            id=self.next_id,
            session_id=kwargs["session_id"],
            answer_id=kwargs["answer_id"],
            question_id=kwargs["question_id"],
            competency_reference=kwargs["competency_reference"],
            weighted_score=kwargs["weighted_score"],
            strengths=kwargs["strengths"],
            improvement_areas=kwargs["improvement_areas"],
            actionable_feedback=kwargs["actionable_feedback"],
            evaluation_status="complete",
            provider_name=kwargs["provider_name"],
            created_at=now,
            updated_at=now,
            criteria=[SimpleNamespace(id=index, **row) for index, row in enumerate(
                kwargs["criterion_rows"], start=1
            )],
        )
        self.next_id += 1
        self.evaluations.append(evaluation)
        return evaluation


@pytest.fixture
def evaluation_context(monkeypatch):
    record, blueprint, analysis, job = _context()
    execution_repository = SimpleNamespace(
        get_by_id=lambda session_id: record if session_id == record.id else None
    )
    evaluation_repository = FakeEvaluationRepository()
    monkeypatch.setattr(
        service_module,
        "InterviewExecutionRepository",
        lambda session: execution_repository,
    )
    monkeypatch.setattr(
        service_module,
        "InterviewEvaluationRepository",
        lambda session: evaluation_repository,
    )
    monkeypatch.setattr(
        service_module,
        "InterviewBlueprintRepository",
        lambda session: SimpleNamespace(
            get_by_id=lambda blueprint_id: blueprint
        ),
    )
    monkeypatch.setattr(
        service_module,
        "ResumeAnalysisRepository",
        lambda session: SimpleNamespace(
            get_by_resume_id=lambda resume_id: analysis
        ),
    )
    monkeypatch.setattr(
        service_module,
        "JobRepository",
        lambda session: SimpleNamespace(get_by_id=lambda job_id: job),
    )
    return record, blueprint, evaluation_repository


def test_valid_evaluation_uses_weighted_rubric_and_is_idempotent(evaluation_context):
    _, _, repository = evaluation_context
    provider = FakeProvider(_provider_payload())
    service = InterviewEvaluationScorecardService(object())

    first = service.evaluate_answer(session_id=7, answer_id=101, provider=provider)
    second = service.evaluate_answer(session_id=7, answer_id=101, provider=provider)

    assert first.weighted_score == pytest.approx(3.2)
    assert len(first.criteria) == 2
    assert first.provider_name == "FakeProvider"
    assert second.id == first.id
    assert provider.calls == 1
    assert len(repository.evaluations) == 1


@pytest.mark.parametrize(
    "response",
    [
        "not-json",
        _provider_payload(scores=(6, 2)),
        _provider_payload().replace(
            '"criterion_id":"depth"', '"criterion_id":"unknown"'
        ),
        _provider_payload().replace(
            '"criterion_id":"depth"', '"criterion_id":"correctness"'
        ),
        _provider_payload().replace(
            '"evidence_excerpts":["before persistence"]',
            '"evidence_excerpts":["not in answer"]',
        ),
    ],
)
def test_invalid_provider_output_is_rejected_without_persistence(
    evaluation_context,
    response,
):
    _, _, repository = evaluation_context
    with pytest.raises(InterviewEvaluationProviderError):
        InterviewEvaluationScorecardService(object()).evaluate_answer(
            session_id=7,
            answer_id=101,
            provider=FakeProvider(response),
        )
    assert repository.evaluations == []


def test_invalid_provider_output_is_retried_once(evaluation_context):
    _, _, repository = evaluation_context
    provider = SequenceProvider(["not-json", _provider_payload()])

    result = InterviewEvaluationScorecardService(object()).evaluate_answer(
        session_id=7,
        answer_id=101,
        provider=provider,
    )

    assert result.answer_id == 101
    assert provider.calls == 2
    assert len(repository.evaluations) == 1


def test_invalid_provider_output_is_not_retried_more_than_once(
    evaluation_context,
):
    _, _, repository = evaluation_context
    provider = SequenceProvider(["not-json", "still-not-json"])

    with pytest.raises(InterviewEvaluationProviderError):
        InterviewEvaluationScorecardService(object()).evaluate_answer(
            session_id=7,
            answer_id=101,
            provider=provider,
        )

    assert provider.calls == 2
    assert repository.evaluations == []


def test_provider_unavailable_is_not_retried(evaluation_context):
    _, _, repository = evaluation_context
    provider = UnavailableProvider()

    with pytest.raises(OllamaProviderUnavailableError):
        InterviewEvaluationScorecardService(object()).evaluate_answer(
            session_id=7,
            answer_id=101,
            provider=provider,
        )

    assert provider.calls == 1
    assert repository.evaluations == []


def test_missing_rubric_is_rejected(evaluation_context):
    _, blueprint, repository = evaluation_context
    blueprint.questions[0].rubric_criteria = []
    blueprint.rubric = []

    with pytest.raises(InterviewEvaluationError):
        InterviewEvaluationScorecardService(object()).evaluate_answer(
            session_id=7,
            answer_id=101,
            provider=FakeProvider(_provider_payload()),
        )
    assert repository.evaluations == []


def test_missing_session_and_answer_are_domain_errors(evaluation_context):
    record, _, _ = evaluation_context
    service = InterviewEvaluationScorecardService(object())

    with pytest.raises(InterviewExecutionSessionNotFoundError):
        service.evaluate_answer(session_id=999, answer_id=101, provider=FakeProvider("{}"))

    record.answers.clear()
    with pytest.raises(InterviewAnswerNotFoundForEvaluationError):
        service.evaluate_answer(session_id=7, answer_id=101, provider=FakeProvider("{}"))


def test_scorecard_is_partial_and_tracks_pending_answers(evaluation_context):
    record, blueprint, repository = evaluation_context
    second_question = SimpleNamespace(
        id=12,
        blueprint_question_id=22,
        question="Explain testing.",
        question_category="technical",
        difficulty="medium",
        target_competency="Backend design",
        assessment_objective="Assess testing.",
        relevance_reason="Testing matters.",
        rubric_criteria=["correctness", "depth"],
        is_follow_up=False,
        parent_question_id=None,
    )
    record.questions.append(second_question)
    record.answers.append(
        SimpleNamespace(
            id=102,
            session_id=7,
            session_question_id=12,
            answer="I would add tests.",
        )
    )

    service = InterviewEvaluationScorecardService(object())
    service.evaluate_answer(
        session_id=7,
        answer_id=101,
        provider=FakeProvider(_provider_payload()),
    )
    scorecard = service.get_scorecard(7)

    assert scorecard.status == "partial"
    assert scorecard.evaluated_answer_count == 1
    assert scorecard.pending_answer_ids == [102]
    assert scorecard.overall_score == pytest.approx(3.2)
    assert len(scorecard.answer_evaluations) == 1
