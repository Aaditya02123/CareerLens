from types import SimpleNamespace

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.interview_execution import (
    InterviewExecutionSession,
    InterviewExecutionStatus,
    InterviewSessionQuestion,
)
from app.repositories.interview_execution_repository import (
    InterviewExecutionRepository,
)


class FakeSession:
    def __init__(self):
        self.statements = []

    def scalar(self, statement):
        self.statements.append(statement)
        return SimpleNamespace()


class FailingCommitSession(FakeSession):
    def __init__(self):
        super().__init__()
        self.rollback_called = False

    def add(self, value):
        pass

    def commit(self):
        raise SQLAlchemyError("commit failed")

    def rollback(self):
        self.rollback_called = True

    def refresh(self, value):
        pass


def test_session_lock_query_uses_for_update():
    session = FakeSession()
    repository = InterviewExecutionRepository(session)

    repository.get_by_id_for_update(7)

    assert "FOR UPDATE" in str(session.statements[0]).upper()


def test_answer_commit_failure_rolls_back_transaction():
    session = FailingCommitSession()
    repository = InterviewExecutionRepository(session)
    execution_session = InterviewExecutionSession(
        id=1,
        blueprint_id=2,
        status=InterviewExecutionStatus.IN_PROGRESS,
        total_questions=1,
        answered_questions=0,
    )
    question = InterviewSessionQuestion(
        id=3,
        session_id=1,
        blueprint_question_id=4,
        question_order=1,
        question="Question",
        question_category="technical",
        difficulty="medium",
        target_competency="Python",
        assessment_objective="Assess reasoning",
        relevance_reason="Required.",
    )

    with pytest.raises(SQLAlchemyError):
        repository.create_answer_and_advance(
            session_record=execution_session,
            question=question,
            answer_text="Answer",
        )

    assert session.rollback_called is True
