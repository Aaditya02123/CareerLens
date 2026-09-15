from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models.interview_session import (
    InterviewAnswerCreate,
    InterviewSessionCreate,
    InterviewSessionStatus,
)
from app.services import interview_session_service as service_module
from app.services.interview_session_service import (
    InactiveInterviewSessionError,
    InterviewSessionNotFoundError,
    InterviewSessionService,
    JobNotFoundError,
    ResumeNotFoundError,
    ResumeOwnershipError,
    UserNotFoundError,
)


class FakeUserRepository:
    def __init__(self, user=None):
        self.user = user

    def get_by_id(self, user_id: int):
        if self.user is not None and self.user.id == user_id:
            return self.user
        return None


class FakeResumeRepository:
    def __init__(self, resumes=None):
        self.resumes = resumes or []

    def get_by_id(self, resume_id: int):
        return next(
            (
                resume
                for resume in self.resumes
                if resume.id == resume_id
            ),
            None,
        )


class FakeJobRepository:
    def __init__(self, jobs=None):
        self.jobs = jobs or []

    def get_by_id(self, job_id: int):
        return next(
            (
                job
                for job in self.jobs
                if job.id == job_id
            ),
            None,
        )


class FakeInterviewSessionRepository:
    def __init__(self):
        self.sessions = {}
        self.answers = {}
        self.next_session_id = 1
        self.next_answer_id = 1

    def create_session(
        self,
        user_id,
        resume_id,
        job_id,
        status,
    ):
        interview_session = SimpleNamespace(
            id=self.next_session_id,
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
            status=status,
            answers=[],
        )
        self.sessions[interview_session.id] = interview_session
        self.answers[interview_session.id] = []
        self.next_session_id += 1
        return interview_session

    def get_by_id(self, session_id: int):
        return self.sessions.get(session_id)

    def list_by_user_id(self, user_id: int):
        return [
            interview_session
            for interview_session in self.sessions.values()
            if interview_session.user_id == user_id
        ]

    def update_status(self, interview_session, status):
        interview_session.status = status
        return interview_session

    def create_answer(
        self,
        session_id,
        question,
        answer,
        question_category,
    ):
        interview_answer = SimpleNamespace(
            id=self.next_answer_id,
            session_id=session_id,
            question=question,
            answer=answer,
            question_category=question_category,
        )
        self.answers[session_id].append(interview_answer)
        self.sessions[session_id].answers.append(interview_answer)
        self.next_answer_id += 1
        return interview_answer

    def list_answers_by_session_id(self, session_id: int):
        return self.answers.get(session_id, [])


@pytest.fixture
def repositories(monkeypatch):
    user = SimpleNamespace(id=1)
    resume = SimpleNamespace(id=1, user_id=1)
    job = SimpleNamespace(id=1)

    user_repository = FakeUserRepository(user=user)
    resume_repository = FakeResumeRepository(resumes=[resume])
    job_repository = FakeJobRepository(jobs=[job])
    interview_repository = FakeInterviewSessionRepository()

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
        "InterviewSessionRepository",
        lambda session: interview_repository,
    )

    return {
        "user": user,
        "resume": resume,
        "job": job,
        "user_repository": user_repository,
        "resume_repository": resume_repository,
        "job_repository": job_repository,
        "interview_repository": interview_repository,
    }


def test_create_session_creates_active_session(repositories):
    service = InterviewSessionService(object())

    interview_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )

    assert interview_session.status == InterviewSessionStatus.ACTIVE
    assert interview_session.user_id == 1
    assert interview_session.resume_id == 1
    assert interview_session.job_id == 1


@pytest.mark.parametrize(
    ("missing_repository", "expected_error"),
    [
        ("user_repository", UserNotFoundError),
        ("resume_repository", ResumeNotFoundError),
        ("job_repository", JobNotFoundError),
    ],
)
def test_create_session_rejects_missing_resources(
    repositories,
    missing_repository,
    expected_error,
):
    repository = repositories[missing_repository]

    if missing_repository == "user_repository":
        repository.user = None
    elif missing_repository == "resume_repository":
        repository.resumes = []
    else:
        repository.jobs = []

    service = InterviewSessionService(object())

    with pytest.raises(expected_error):
        service.create_session(
            InterviewSessionCreate(
                user_id=1,
                resume_id=1,
                job_id=1,
            )
        )


def test_create_session_rejects_resume_owned_by_another_user(
    repositories,
):
    repositories["resume"].user_id = 2
    service = InterviewSessionService(object())

    with pytest.raises(ResumeOwnershipError):
        service.create_session(
            InterviewSessionCreate(
                user_id=1,
                resume_id=1,
                job_id=1,
            )
        )


def test_existing_session_can_be_retrieved(repositories):
    service = InterviewSessionService(object())
    created_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )

    retrieved_session = service.get_session(created_session.id)

    assert retrieved_session.id == created_session.id


def test_missing_session_raises_error(repositories):
    service = InterviewSessionService(object())

    with pytest.raises(InterviewSessionNotFoundError):
        service.get_session(999)


def test_sessions_are_listed_for_user(repositories):
    service = InterviewSessionService(object())

    first_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )
    second_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )

    sessions = service.list_sessions_for_user(1)

    assert [session.id for session in sessions] == [
        first_session.id,
        second_session.id,
    ]


def test_listing_sessions_for_missing_user_raises_error(repositories):
    repositories["user_repository"].user = None
    service = InterviewSessionService(object())

    with pytest.raises(UserNotFoundError):
        service.list_sessions_for_user(1)


@pytest.mark.parametrize(
    ("new_status", "expected_status"),
    [
        (
            "completed",
            InterviewSessionStatus.COMPLETED,
        ),
        (
            "abandoned",
            InterviewSessionStatus.ABANDONED,
        ),
        (
            "active",
            InterviewSessionStatus.ACTIVE,
        ),
    ],
)
def test_active_session_transitions_are_allowed(
    repositories,
    new_status,
    expected_status,
):
    service = InterviewSessionService(object())
    interview_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )

    updated_session = service.update_session_status(
        session_id=interview_session.id,
        new_status=new_status,
    )

    assert updated_session.status == expected_status


@pytest.mark.parametrize(
    ("initial_status", "new_status"),
    [
        ("completed", "active"),
        ("completed", "abandoned"),
        ("abandoned", "active"),
        ("abandoned", "completed"),
    ],
)
def test_terminal_session_transitions_are_rejected(
    repositories,
    initial_status,
    new_status,
):
    service = InterviewSessionService(object())
    interview_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )
    service.update_session_status(
        session_id=interview_session.id,
        new_status=initial_status,
    )

    with pytest.raises(ValueError):
        service.update_session_status(
            session_id=interview_session.id,
            new_status=new_status,
        )


def test_invalid_session_status_is_rejected(repositories):
    service = InterviewSessionService(object())
    interview_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )

    with pytest.raises(ValueError):
        service.update_session_status(
            session_id=interview_session.id,
            new_status="invalid",
        )


def test_valid_answer_preserves_exact_text_and_category(repositories):
    service = InterviewSessionService(object())
    interview_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )

    answer_data = InterviewAnswerCreate(
        question="How would you use FastAPI?",
        answer="I would use FastAPI to build REST APIs.",
        question_category="technical",
    )

    answer = service.submit_answer(
        session_id=interview_session.id,
        answer_data=answer_data,
    )

    assert answer.question == answer_data.question
    assert answer.answer == answer_data.answer
    assert answer.question_category == answer_data.question_category


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("question", ""),
        ("answer", ""),
    ],
)
def test_empty_question_or_answer_is_rejected(
    repositories,
    field,
    value,
):
    service = InterviewSessionService(object())
    interview_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )

    values = {
        "question": "A valid question",
        "answer": "A valid answer",
        "question_category": "technical",
    }
    values[field] = value

    answer_data = InterviewAnswerCreate.model_construct(**values)

    with pytest.raises(ValueError):
        service.submit_answer(
            session_id=interview_session.id,
            answer_data=answer_data,
        )


def test_empty_category_is_rejected_at_service_level(repositories):
    service = InterviewSessionService(object())
    interview_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )

    answer_data = InterviewAnswerCreate.model_construct(
        question="A valid question",
        answer="A valid answer",
        question_category="",
    )

    with pytest.raises(ValueError):
        service.submit_answer(
            session_id=interview_session.id,
            answer_data=answer_data,
        )


def test_invalid_question_category_is_rejected_by_pydantic():
    with pytest.raises(ValidationError):
        InterviewAnswerCreate(
            question="How would you use FastAPI?",
            answer="I would use FastAPI to build REST APIs.",
            question_category="unknown",
        )


@pytest.mark.parametrize(
    "terminal_status",
    [
        "completed",
        "abandoned",
    ],
)
def test_answer_submission_to_inactive_session_is_rejected(
    repositories,
    terminal_status,
):
    service = InterviewSessionService(object())
    interview_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )
    service.update_session_status(
        session_id=interview_session.id,
        new_status=terminal_status,
    )

    answer_data = InterviewAnswerCreate(
        question="Tell me about yourself.",
        answer="I am a software developer.",
        question_category="behavioral",
    )

    with pytest.raises(InactiveInterviewSessionError):
        service.submit_answer(
            session_id=interview_session.id,
            answer_data=answer_data,
        )


def test_answers_are_retrieved_in_creation_order(repositories):
    service = InterviewSessionService(object())
    interview_session = service.create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )

    first_answer = service.submit_answer(
        session_id=interview_session.id,
        answer_data=InterviewAnswerCreate(
            question="First question",
            answer="First answer",
            question_category="technical",
        ),
    )
    second_answer = service.submit_answer(
        session_id=interview_session.id,
        answer_data=InterviewAnswerCreate(
            question="Second question",
            answer="Second answer",
            question_category="behavioral",
        ),
    )

    answers = service.list_answers(interview_session.id)

    assert [answer.id for answer in answers] == [
        first_answer.id,
        second_answer.id,
    ]