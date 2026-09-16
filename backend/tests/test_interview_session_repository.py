from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories import interview_session_repository as repository_module
from app.repositories.interview_session_repository import (
    DuplicateInterviewAnswerError,
    InterviewSessionRepository,
)


class FakeSession:
    def __init__(self, commit_error=None):
        self.commit_error = commit_error
        self.rollback_called = False
        self.added = []

    def add(self, value):
        self.added.append(value)

    def commit(self):
        if self.commit_error is not None:
            raise self.commit_error

    def rollback(self):
        self.rollback_called = True

    def refresh(self, value):
        return None


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