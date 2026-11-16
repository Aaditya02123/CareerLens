from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.interview_execution import (
    InterviewExecutionStatus,
    InterviewSessionAnswerCreate,
)
from app.services import interview_execution_service as service_module
from app.services.interview_execution_service import (
    EmptyInterviewBlueprintError,
    InterviewExecutionAnswerError,
    InterviewExecutionBlueprintNotFoundError,
    InterviewExecutionSessionNotFoundError,
    InterviewExecutionService,
    InvalidInterviewExecutionTransitionError,
)


def _question(question_id, order):
    return SimpleNamespace(
        id=question_id,
        blueprint_question_id=question_id + 100,
        question_order=order,
        question=f"Question {order}",
        question_category="technical",
        difficulty="medium",
        target_competency="Python",
        assessment_objective="Assess reasoning",
        relevance_reason="Python is required.",
    )


def _blueprint(question_count=3):
    return SimpleNamespace(
        id=4,
        questions=[
            _question(index, index)
            for index in range(1, question_count + 1)
        ],
    )


class FakeRepository:
    def __init__(self, blueprint=None):
        self.blueprint = blueprint
        self.sessions = {}
        self.next_id = 1

    def get_blueprint(self, blueprint_id):
        return self.blueprint if self.blueprint and blueprint_id == 4 else None

    def create_from_blueprint(self, blueprint):
        record = SimpleNamespace(
            id=self.next_id,
            blueprint_id=blueprint.id,
            status=InterviewExecutionStatus.CREATED,
            total_questions=len(blueprint.questions),
            answered_questions=0,
            created_at=datetime.now(timezone.utc),
            started_at=None,
            completed_at=None,
            questions=list(blueprint.questions),
            answers=[],
        )
        self.next_id += 1
        self.sessions[record.id] = record
        return record

    def get_by_id(self, session_id):
        return self.sessions.get(session_id)

    def get_next_unanswered_question(self, record):
        answered = {answer.session_question_id for answer in record.answers}
        return next(
            (item for item in record.questions if item.id not in answered),
            None,
        )

    def start(self, record):
        record.status = InterviewExecutionStatus.IN_PROGRESS
        record.started_at = datetime.now(timezone.utc)
        return record

    def create_answer_and_advance(self, session_record, question, answer_text):
        answer = SimpleNamespace(
            id=len(session_record.answers) + 1,
            session_id=session_record.id,
            session_question_id=question.id,
            question_order=question.question_order,
            answer=answer_text,
            submitted_at=datetime.now(timezone.utc),
        )
        session_record.answers.append(answer)
        session_record.answered_questions += 1
        if session_record.answered_questions == session_record.total_questions:
            session_record.status = InterviewExecutionStatus.COMPLETED
            session_record.completed_at = datetime.now(timezone.utc)
        return answer


@pytest.fixture
def service(monkeypatch):
    repository = FakeRepository(_blueprint())
    monkeypatch.setattr(
        service_module,
        "InterviewExecutionRepository",
        lambda session: repository,
    )
    return InterviewExecutionService(object()), repository


def test_create_session_snapshots_questions_in_order(service):
    execution, _ = service
    result = execution.create_session(4)

    assert result.status == InterviewExecutionStatus.CREATED
    assert result.total_questions == 3
    assert result.answered_questions == 0
    assert result.current_question_position == 1
    assert result.next_question.question == "Question 1"


def test_missing_or_empty_blueprint_is_rejected(monkeypatch):
    missing = FakeRepository(None)
    monkeypatch.setattr(
        service_module,
        "InterviewExecutionRepository",
        lambda session: missing,
    )
    with pytest.raises(InterviewExecutionBlueprintNotFoundError):
        InterviewExecutionService(object()).create_session(4)

    empty = FakeRepository(_blueprint(0))
    monkeypatch.setattr(
        service_module,
        "InterviewExecutionRepository",
        lambda session: empty,
    )
    with pytest.raises(EmptyInterviewBlueprintError):
        InterviewExecutionService(object()).create_session(4)


def test_lifecycle_and_resume_preserve_progress(service):
    execution, _ = service
    created = execution.create_session(4)
    started = execution.start_session(created.id)
    assert started.status == InterviewExecutionStatus.IN_PROGRESS

    with pytest.raises(InvalidInterviewExecutionTransitionError):
        execution.start_session(created.id)

    after_answer = execution.submit_answer(
        created.id,
        InterviewSessionAnswerCreate(answer="First answer"),
    )
    resumed = execution.get_session(created.id)
    assert after_answer.answered_questions == 1
    assert resumed.answered_questions == 1
    assert resumed.current_question_position == 2
    assert len(resumed.answers) == 1


def test_answers_require_started_session_and_nonempty_text(service):
    execution, _ = service
    created = execution.create_session(4)

    with pytest.raises(InvalidInterviewExecutionTransitionError):
        execution.submit_answer(
            created.id,
            InterviewSessionAnswerCreate(answer="Answer"),
        )

    execution.start_session(created.id)
    with pytest.raises(InterviewExecutionAnswerError):
        execution.submit_answer(
            created.id,
            InterviewSessionAnswerCreate.model_construct(answer="   "),
        )


def test_final_answer_completes_session_and_rejects_more_answers(service):
    execution, _ = service
    created = execution.create_session(4)
    execution.start_session(created.id)

    for index in range(3):
        result = execution.submit_answer(
            created.id,
            InterviewSessionAnswerCreate(answer=f"Answer {index}"),
        )

    assert result.status == InterviewExecutionStatus.COMPLETED
    assert result.current_question_position is None
    assert result.completion_percentage == pytest.approx(100.0)

    with pytest.raises(InvalidInterviewExecutionTransitionError):
        execution.submit_answer(
            created.id,
            InterviewSessionAnswerCreate(answer="Extra"),
        )


def test_missing_session_is_rejected(service):
    execution, _ = service
    with pytest.raises(InterviewExecutionSessionNotFoundError):
        execution.get_session(999)
