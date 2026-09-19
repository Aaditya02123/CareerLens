from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories import interview_session_repository as repository_module
from app.repositories.interview_session_repository import (
    DuplicateInterviewAnswerError,
    InterviewSessionRepository,
)


class FakeSession:
    def __init__(self, commit_error=None, scalar_result=None):
        self.commit_error = commit_error
        self.scalar_result = scalar_result
        self.rollback_called = False
        self.added = []
        self.scalar_statements = []

    def add(self, value):
        self.added.append(value)

    def commit(self):
        if self.commit_error is not None:
            raise self.commit_error

    def rollback(self):
        self.rollback_called = True

    def refresh(self, value):
        return None

    def scalar(self, statement):
        self.scalar_statements.append(statement)
        return self.scalar_result


class FakeUniqueViolation(Exception):
    def __init__(self, constraint_name):
        self.diag = SimpleNamespace(
            constraint_name=constraint_name
        )


def make_integrity_error(orig):
    return IntegrityError(
        "insert failed",
        {},
        orig,
    )


def make_question():
    return SimpleNamespace(
        id=10,
        question="Persisted question",
        question_category="technical",
    )


def test_named_unique_violation_is_translated(monkeypatch):
    monkeypatch.setattr(
        repository_module,
        "UniqueViolation",
        FakeUniqueViolation,
    )

    error = make_integrity_error(
        FakeUniqueViolation(
            "uq_interview_answers_session_question"
        )
    )
    session = FakeSession(commit_error=error)
    repository = InterviewSessionRepository(session)

    with pytest.raises(DuplicateInterviewAnswerError):
        repository.create_answer(
            session_id=1,
            question=make_question(),
            answer="Answer.",
        )

    assert session.rollback_called is True
    assert session.added


def test_unrelated_integrity_error_is_not_translated(monkeypatch):
    monkeypatch.setattr(
        repository_module,
        "UniqueViolation",
        FakeUniqueViolation,
    )

    error = make_integrity_error(
        FakeUniqueViolation("some_other_constraint")
    )
    session = FakeSession(commit_error=error)
    repository = InterviewSessionRepository(session)

    with pytest.raises(IntegrityError) as raised:
        repository.create_answer(
            session_id=1,
            question=make_question(),
            answer="Answer.",
        )

    assert raised.value is error


def test_get_next_unanswered_question_returns_scalar_result():
    question = make_question()
    session = FakeSession(scalar_result=question)
    repository = InterviewSessionRepository(session)

    result = repository.get_next_unanswered_question(session_id=1)

    assert result is question
    assert session.scalar_statements


def test_get_next_unanswered_question_returns_none_when_no_match():
    session = FakeSession(scalar_result=None)
    repository = InterviewSessionRepository(session)

    result = repository.get_next_unanswered_question(session_id=1)

    assert result is None
    assert session.scalar_statements


def test_get_next_unanswered_question_uses_not_exists_query():
    session = FakeSession(scalar_result=None)
    repository = InterviewSessionRepository(session)

    repository.get_next_unanswered_question(session_id=1)

    compiled_statement = str(session.scalar_statements[0]).upper()

    assert "NOT" in compiled_statement
    assert "EXISTS" in compiled_statement
    assert "ORDER BY" in compiled_statement


@pytest.mark.parametrize(
    ("method_name", "expected_count"),
    [
        ("count_questions_by_session_id", 10),
        ("count_answers_by_session_id", 6),
    ],
)
def test_count_methods_return_scalar_count(
    method_name,
    expected_count,
):
    session = FakeSession(scalar_result=expected_count)
    repository = InterviewSessionRepository(session)

    result = getattr(repository, method_name)(session_id=1)

    assert result == expected_count
    assert session.scalar_statements


@pytest.mark.parametrize(
    "method_name",
    [
        "count_questions_by_session_id",
        "count_answers_by_session_id",
    ],
)
def test_count_methods_return_zero_when_scalar_is_none(method_name):
    session = FakeSession(scalar_result=None)
    repository = InterviewSessionRepository(session)

    result = getattr(repository, method_name)(session_id=1)

    assert result == 0


@pytest.mark.parametrize(
    "method_name",
    [
        "count_questions_by_session_id",
        "count_answers_by_session_id",
    ],
)
def test_count_methods_use_count_and_session_filter(method_name):
    session = FakeSession(scalar_result=0)
    repository = InterviewSessionRepository(session)

    getattr(repository, method_name)(session_id=1)

    compiled_statement = str(session.scalar_statements[0]).upper()

    assert "COUNT" in compiled_statement
    assert "WHERE" in compiled_statement