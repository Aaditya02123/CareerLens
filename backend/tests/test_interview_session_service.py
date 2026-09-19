from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models.interview_preparation import (
    InterviewPreparationResponse,
)
from app.models.interview_session import (
    InterviewAnswerCreate,
    InterviewSessionCreate,
    InterviewSessionStatus,
)
from app.services import interview_session_service as service_module
from app.services.interview_session_service import (
    InactiveInterviewSessionError,
    InterviewQuestionNotFoundError,
    InterviewQuestionOwnershipError,
    InterviewSessionNotFoundError,
    InterviewSessionService,
    InvalidInterviewSessionStatusTransitionError,
    JobNotFoundError,
    ResumeNotFoundError,
    ResumeOwnershipError,
    UserNotFoundError,
)


class FakeRepository:
    def __init__(self):
        self.session = object()
        self.sessions = {}
        self.questions = {}
        self.answers = {}
        self.next_session_id = 1
        self.next_question_id = 1
        self.next_answer_id = 1

    def create_session_with_questions(
        self,
        user_id,
        resume_id,
        job_id,
        status,
        questions,
    ):
        session = SimpleNamespace(
            id=self.next_session_id,
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
            status=status,
            answers=[],
        )
        self.sessions[session.id] = session
        self.questions[session.id] = []

        for generated in questions:
            question = SimpleNamespace(
                id=self.next_question_id,
                session_id=session.id,
                question=generated.question,
                category=generated.category,
                question_category=generated.category,
            )
            self.questions[session.id].append(question)
            self.next_question_id += 1

        self.answers[session.id] = []
        self.next_session_id += 1
        return session

    def get_by_id(self, session_id):
        return self.sessions.get(session_id)

    def list_by_user_id(self, user_id):
        return [
            item
            for item in self.sessions.values()
            if item.user_id == user_id
        ]

    def update_status(self, interview_session, status):
        interview_session.status = status
        return interview_session

    def get_question_by_id(self, question_id):
        for questions in self.questions.values():
            for question in questions:
                if getattr(question, "id", None) == question_id:
                    return question
        return None

    def create_answer(self, session_id, question, answer):
        item = SimpleNamespace(
            id=self.next_answer_id,
            session_id=session_id,
            question_id=question.id,
            question=question.question,
            answer=answer,
            question_category=question.category,
        )
        self.answers[session_id].append(item)
        self.next_answer_id += 1
        return item

    def answer_exists_for_question(
        self,
        session_id: int,
        question_id: int,
    ) -> bool:
        return any(
            answer.question_id == question_id
            for answer in self.answers.get(session_id, [])
        )

    def count_questions_by_session_id(self, session_id):
        return len(self.questions.get(session_id, []))

    def count_answers_by_session_id(self, session_id):
        return len(self.answers.get(session_id, []))

    def list_answers_by_session_id(self, session_id):
        return self.answers.get(session_id, [])


class FakeUserRepository:
    def __init__(self, user=None):
        self.user = user

    def get_by_id(self, user_id):
        return self.user


class FakeResumeRepository:
    def __init__(self, resume=None):
        self.resume = resume

    def get_by_id(self, resume_id):
        return self.resume


class FakeJobRepository:
    def __init__(self, job=None):
        self.job = job

    def get_by_id(self, job_id):
        return self.job


@pytest.fixture
def repositories(monkeypatch):
    repository = FakeRepository()
    user_repository = FakeUserRepository(SimpleNamespace(id=1))
    resume_repository = FakeResumeRepository(
        SimpleNamespace(id=1, user_id=1)
    )
    job_repository = FakeJobRepository(SimpleNamespace(id=1))

    monkeypatch.setattr(
        service_module,
        "InterviewSessionRepository",
        lambda session: repository,
    )
    monkeypatch.setattr(
        service_module,
        "UserRepository",
        lambda session: user_repository,
    )
    monkeypatch.setattr(
        service_module,
        "ResumeRepository",
        lambda session: resume_repository,
    )
    monkeypatch.setattr(
        service_module,
        "JobRepository",
        lambda session: job_repository,
    )
    monkeypatch.setattr(
        service_module,
        "build_interview_preparation",
        lambda **kwargs: InterviewPreparationResponse(
            resume_id=1,
            job_id=1,
            questions=[],
        ),
    )

    return {
        "repository": repository,
        "user": user_repository,
        "resume": resume_repository,
        "job": job_repository,
    }


def create_session(repositories):
    return InterviewSessionService(object()).create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )


def add_questions(repository, session_id, count):
    for index in range(count):
        repository.questions[session_id].append(
            SimpleNamespace(
                id=repository.next_question_id,
                session_id=session_id,
                question=f"Question {index + 1}",
                category="technical",
                question_category="technical",
            )
        )
        repository.next_question_id += 1


def answer_questions(repository, session_id, count):
    for question in repository.questions[session_id][:count]:
        repository.create_answer(
            session_id=session_id,
            question=question,
            answer=f"Answer for question {question.id}",
        )


def test_create_session_is_active(repositories):
    session = create_session(repositories)
    assert session.status == InterviewSessionStatus.ACTIVE


@pytest.mark.parametrize(
    ("name", "error"),
    [
        ("user", UserNotFoundError),
        ("resume", ResumeNotFoundError),
        ("job", JobNotFoundError),
    ],
)
def test_create_session_validates_resources(
    repositories,
    name,
    error,
):
    if name == "user":
        repositories["user"].user = None
    elif name == "resume":
        repositories["resume"].resume = None
    elif name == "job":
        repositories["job"].job = None

    with pytest.raises(error):
        create_session(repositories)


def test_create_session_rejects_resume_owned_by_another_user(
    repositories,
):
    repositories["resume"].resume.user_id = 2

    with pytest.raises(ResumeOwnershipError):
        create_session(repositories)


def test_session_retrieval_and_listing(repositories):
    first = create_session(repositories)
    second = create_session(repositories)

    service = InterviewSessionService(object())

    assert service.get_session(first.id).id == first.id
    assert [item.id for item in service.list_sessions_for_user(1)] == [
        first.id,
        second.id,
    ]


def test_missing_session_is_rejected(repositories):
    with pytest.raises(InterviewSessionNotFoundError):
        InterviewSessionService(object()).get_session(999)


def test_progress_for_unanswered_session(repositories):
    session = create_session(repositories)
    add_questions(repositories["repository"], session.id, 10)

    result = InterviewSessionService(object()).get_session_progress(
        session.id
    )

    assert result.session_id == session.id
    assert result.status == InterviewSessionStatus.ACTIVE
    assert result.total_questions == 10
    assert result.answered_questions == 0
    assert result.remaining_questions == 10
    assert result.progress_percentage == pytest.approx(0.0)


def test_progress_for_partially_answered_session(repositories):
    session = create_session(repositories)
    add_questions(repositories["repository"], session.id, 10)
    answer_questions(repositories["repository"], session.id, 6)

    result = InterviewSessionService(object()).get_session_progress(
        session.id
    )

    assert result.total_questions == 10
    assert result.answered_questions == 6
    assert result.remaining_questions == 4
    assert result.progress_percentage == pytest.approx(60.0)


def test_progress_for_fully_answered_session(repositories):
    session = create_session(repositories)
    add_questions(repositories["repository"], session.id, 10)
    answer_questions(repositories["repository"], session.id, 10)

    result = InterviewSessionService(object()).get_session_progress(
        session.id
    )

    assert result.total_questions == 10
    assert result.answered_questions == 10
    assert result.remaining_questions == 0
    assert result.progress_percentage == pytest.approx(100.0)


def test_progress_for_zero_question_session(repositories):
    session = create_session(repositories)

    result = InterviewSessionService(object()).get_session_progress(
        session.id
    )

    assert result.total_questions == 0
    assert result.answered_questions == 0
    assert result.remaining_questions == 0
    assert result.progress_percentage == pytest.approx(0.0)


def test_progress_ignores_answers_from_other_sessions(repositories):
    first = create_session(repositories)
    second = create_session(repositories)
    add_questions(repositories["repository"], first.id, 10)
    add_questions(repositories["repository"], second.id, 10)
    answer_questions(repositories["repository"], second.id, 6)

    result = InterviewSessionService(object()).get_session_progress(
        first.id
    )

    assert result.total_questions == 10
    assert result.answered_questions == 0
    assert result.remaining_questions == 10
    assert result.progress_percentage == pytest.approx(0.0)


def test_progress_missing_session_is_rejected(repositories):
    with pytest.raises(InterviewSessionNotFoundError):
        InterviewSessionService(object()).get_session_progress(999)


@pytest.mark.parametrize(
    "status",
    [
        InterviewSessionStatus.ACTIVE,
        InterviewSessionStatus.COMPLETED,
        InterviewSessionStatus.ABANDONED,
    ],
)
def test_progress_returns_session_status(repositories, status):
    session = create_session(repositories)
    session.status = status

    result = InterviewSessionService(object()).get_session_progress(
        session.id
    )

    assert result.status == status


@pytest.mark.parametrize(
    ("new_status", "expected"),
    [
        ("completed", InterviewSessionStatus.COMPLETED),
        ("abandoned", InterviewSessionStatus.ABANDONED),
        ("active", InterviewSessionStatus.ACTIVE),
    ],
)
def test_active_status_transitions(
    repositories,
    new_status,
    expected,
):
    session = create_session(repositories)

    result = InterviewSessionService(object()).update_session_status(
        session.id,
        new_status,
    )

    assert result.status == expected


@pytest.mark.parametrize(
    ("initial", "new", "message"),
    [
        (
            "completed",
            "active",
            "Interview session is already completed and cannot "
            "transition to active.",
        ),
        (
            "completed",
            "abandoned",
            "Interview session is already completed and cannot "
            "transition to abandoned.",
        ),
        (
            "abandoned",
            "active",
            "Interview session is already abandoned and cannot "
            "transition to active.",
        ),
        (
            "abandoned",
            "completed",
            "Interview session is already abandoned and cannot "
            "transition to completed.",
        ),
    ],
)
def test_terminal_status_transitions_are_rejected(
    repositories,
    initial,
    new,
    message,
):
    session = create_session(repositories)
    service = InterviewSessionService(object())
    service.update_session_status(session.id, initial)

    with pytest.raises(
        InvalidInterviewSessionStatusTransitionError,
        match=message,
    ):
        service.update_session_status(session.id, new)


def test_invalid_status_is_rejected(repositories):
    session = create_session(repositories)

    with pytest.raises(ValueError):
        InterviewSessionService(object()).update_session_status(
            session.id,
            "invalid",
        )


def test_inactive_session_rejects_answers(repositories):
    session = create_session(repositories)
    service = InterviewSessionService(object())
    service.update_session_status(session.id, "completed")

    with pytest.raises(InactiveInterviewSessionError):
        service.submit_answer(
            session.id,
            InterviewAnswerCreate(
                question_id=1,
                answer="Answer.",
            ),
        )


def test_answer_requires_persisted_question(repositories):
    session = create_session(repositories)

    with pytest.raises(InterviewQuestionNotFoundError):
        InterviewSessionService(object()).submit_answer(
            session.id,
            InterviewAnswerCreate(
                question_id=999,
                answer="Answer.",
            ),
        )


def test_answer_category_is_derived_from_question(repositories):
    question = SimpleNamespace(
        id=1,
        session_id=1,
        question="Persisted question",
        category="technical",
    )
    session = create_session(repositories)
    repositories["repository"].questions[session.id] = [question]

    answer = InterviewSessionService(object()).submit_answer(
        session.id,
        InterviewAnswerCreate(
            question_id=1,
            answer="Exact answer text.",
        ),
    )

    assert answer.question == "Persisted question"
    assert answer.question_category == "technical"


def test_cross_session_question_is_rejected(repositories):
    first = create_session(repositories)
    second = create_session(repositories)

    question = SimpleNamespace(
        id=10,
        session_id=first.id,
        question="First session question",
        category="technical",
    )
    repositories["repository"].questions[first.id] = [question]

    with pytest.raises(InterviewQuestionOwnershipError):
        InterviewSessionService(object()).submit_answer(
            second.id,
            InterviewAnswerCreate(
                question_id=10,
                answer="Cross-session answer.",
            ),
        )


def test_empty_answer_is_rejected(repositories):
    session = create_session(repositories)

    with pytest.raises(ValueError):
        InterviewSessionService(object()).submit_answer(
            session.id,
            InterviewAnswerCreate.model_construct(
                question_id=1,
                answer="",
            ),
        )


def test_invalid_answer_schema_is_rejected():
    with pytest.raises(ValidationError):
        InterviewAnswerCreate(
            question_id=1,
            answer=None,
        )