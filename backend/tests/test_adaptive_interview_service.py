from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.models.interview_execution import InterviewExecutionStatus
from app.services import adaptive_interview_service as service_module
from app.services.adaptive_interview_service import (
    AdaptiveInterviewService,
    AdaptiveProviderError,
    AdaptiveQuestionError,
)
from app.services.interview_execution_service import (
    InterviewExecutionSessionNotFoundError,
)


def question(question_id=1, order=1, follow_up=False):
    return SimpleNamespace(
        id=question_id,
        blueprint_question_id=None if follow_up else question_id + 100,
        question_order=order if not follow_up else order * 1000 + 1,
        conversation_order=Decimal("1.5") if follow_up else Decimal(order),
        question="Explain the Python API design.",
        question_category="technical",
        difficulty="medium",
        target_competency="Python",
        assessment_objective="Assess reasoning",
        relevance_reason="Follow-up context.",
        is_follow_up=follow_up,
        parent_question_id=1 if follow_up else None,
    )


class FakeProvider:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def generate(self, system_prompt, prompt):
        self.calls += 1
        return self.response


class FakeRepository:
    def __init__(self):
        self.parent = question()
        self.record = SimpleNamespace(
            id=7,
            blueprint_id=4,
            status=InterviewExecutionStatus.IN_PROGRESS,
            questions=[self.parent, question(2, 2)],
            answers=[
                SimpleNamespace(
                    id=10,
                    session_id=7,
                    session_question_id=1,
                    answer="I used Python for the API.",
                    question_order=1,
                    conversation_order=Decimal("1"),
                )
            ],
            total_questions=2,
            answered_questions=1,
        )
        self.decisions = {}
        self.next_id = 20

    def get_by_id(self, session_id):
        return self.record if session_id == 7 else None

    def get_by_id_for_update(self, session_id):
        return self.get_by_id(session_id)

    def get_question_by_id(self, record, question_id):
        return next(
            (item for item in record.questions if item.id == question_id),
            None,
        )

    def get_answer_by_question(self, session_id, question_id):
        return next(
            (
                item
                for item in self.record.answers
                if item.session_question_id == question_id
            ),
            None,
        )

    def get_adaptive_decision(self, session_id, parent_question_id):
        return self.decisions.get((session_id, parent_question_id))

    def create_adaptive_decision(
        self,
        *,
        session_record,
        parent_question,
        outcome,
        rationale,
        follow_up_type,
        competency_reference,
        follow_up_question,
    ):
        follow_up_id = None
        if follow_up_question is not None:
            follow_up_id = self.next_id
            self.next_id += 1
            follow_up = SimpleNamespace(
                id=follow_up_id,
                blueprint_question_id=None,
                question_order=1001,
                conversation_order=Decimal("1.5"),
                question=follow_up_question["question"],
                question_category=follow_up_question["question_category"],
                difficulty=follow_up_question["difficulty"],
                target_competency=follow_up_question["target_competency"],
                assessment_objective=follow_up_question["assessment_objective"],
                relevance_reason=follow_up_question["relevance_reason"],
                is_follow_up=True,
                parent_question_id=parent_question.id,
            )
            session_record.questions.append(follow_up)
            session_record.total_questions += 1
        decision = SimpleNamespace(
            id=self.next_id,
            session_id=session_record.id,
            parent_question_id=parent_question.id,
            outcome=outcome,
            rationale=rationale,
            follow_up_type=follow_up_type,
            competency_reference=competency_reference,
            follow_up_question_id=follow_up_id,
        )
        self.decisions[(session_record.id, parent_question.id)] = decision
        return decision


@pytest.fixture
def adaptive_context(monkeypatch):
    repository = FakeRepository()
    blueprint = SimpleNamespace(
        id=4,
        resume_id=1,
        job_id=2,
        competencies=[SimpleNamespace(name="Python")],
    )
    analysis = SimpleNamespace(
        structured_resume={"skills": ["Python"]},
        categorized_skills={
            "skills": [{"name": "Python", "category": "Programming Language"}]
        },
    )
    job = SimpleNamespace(
        title="Backend Engineer",
        description="Build Python APIs.",
        required_skills=["Python"],
        preferred_skills=[],
    )

    monkeypatch.setattr(
        service_module,
        "InterviewExecutionRepository",
        lambda session: repository,
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
    return repository


def ask_payload():
    return (
        '{"outcome":"ask_follow_up",'
        '"rationale":"The implementation detail needs clarification.",'
        '"follow_up_question":"What trade-off did you consider for this API design?",'
        '"follow_up_type":"deeper_exploration",'
        '"competency_reference":"Python"}'
    )


def test_ask_follow_up_is_persisted_after_answer(adaptive_context):
    provider = FakeProvider(ask_payload())
    result = AdaptiveInterviewService(object()).decide_after_answer(
        session_id=7,
        parent_question_id=1,
        provider=provider,
    )

    assert result.outcome == "ask_follow_up"
    assert result.follow_up_question.is_follow_up is True
    assert result.follow_up_question.parent_question_id == 1
    assert provider.calls == 1


def test_continue_decision_has_no_follow_up(adaptive_context):
    provider = FakeProvider(
        '{"outcome":"continue","rationale":"The answer is sufficient."}'
    )
    result = AdaptiveInterviewService(object()).decide_after_answer(
        session_id=7,
        parent_question_id=1,
        provider=provider,
    )
    assert result.outcome == "continue"
    assert result.follow_up_question is None


def test_decision_is_idempotent_and_provider_is_not_called_twice(
    adaptive_context,
):
    provider = FakeProvider(ask_payload())
    service = AdaptiveInterviewService(object())
    first = service.decide_after_answer(
        session_id=7,
        parent_question_id=1,
        provider=provider,
    )
    second = service.decide_after_answer(
        session_id=7,
        parent_question_id=1,
        provider=provider,
    )
    assert first.outcome == second.outcome
    assert provider.calls == 1


def test_malformed_provider_output_is_rejected_without_persistence(
    adaptive_context,
):
    repository = adaptive_context
    with pytest.raises(AdaptiveProviderError):
        AdaptiveInterviewService(object()).decide_after_answer(
            session_id=7,
            parent_question_id=1,
            provider=FakeProvider("not-json"),
        )
    assert repository.decisions == {}


def test_unsupported_competency_is_rejected(adaptive_context):
    payload = ask_payload().replace("Python", "Unknown")
    with pytest.raises(AdaptiveProviderError):
        AdaptiveInterviewService(object()).decide_after_answer(
            session_id=7,
            parent_question_id=1,
            provider=FakeProvider(payload),
        )


def test_follow_up_limit_returns_continue_without_provider(adaptive_context):
    repository = adaptive_context
    for index in range(3):
        repository.record.questions.append(question(100 + index, index + 3, True))

    provider = FakeProvider(ask_payload())
    result = AdaptiveInterviewService(object()).decide_after_answer(
        session_id=7,
        parent_question_id=1,
        provider=provider,
    )
    assert result.outcome == "continue"
    assert provider.calls == 0


def test_adaptive_decision_rejects_missing_session(adaptive_context):
    with pytest.raises(InterviewExecutionSessionNotFoundError):
        AdaptiveInterviewService(object()).decide_after_answer(
            session_id=999,
            parent_question_id=1,
            provider=FakeProvider(ask_payload()),
        )


def test_adaptive_decision_requires_answered_planned_question(adaptive_context):
    repository = adaptive_context
    repository.record.answers = []
    with pytest.raises(AdaptiveQuestionError):
        AdaptiveInterviewService(object()).decide_after_answer(
            session_id=7,
            parent_question_id=1,
            provider=FakeProvider(ask_payload()),
        )
