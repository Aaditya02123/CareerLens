from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.models.interview_evaluation import InterviewEvaluationResponse
from app.models.interview_preparation import (
    InterviewPreparationResponse,
    InterviewQuestion as GeneratedQuestion,
)
from app.models.interview_session import (
    InterviewAnswerCreate,
    InterviewSessionCreate,
    InterviewSessionStatus,
)
from app.services import interview_report_service
from app.services import interview_session_service as service_module
from app.services.interview_session_service import (
    InterviewQuestionNotFoundError,
    InterviewQuestionOwnershipError,
    InterviewSessionNotFoundError,
    InterviewSessionService,
    NoUnansweredInterviewQuestionError,
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
        )

        self.sessions[session.id] = session

        persisted_questions = []

        for question_order, item in enumerate(questions, start=1):
            persisted_questions.append(
                SimpleNamespace(
                    id=self.next_question_id,
                    session_id=session.id,
                    question=item.question,
                    question_category=item.category,
                    difficulty=item.difficulty,
                    priority=item.priority,
                    reason=item.reason,
                    question_order=question_order,
                    created_at=datetime.now(timezone.utc),
                )
            )

            self.next_question_id += 1

        self.questions[session.id] = persisted_questions
        self.answers[session.id] = []

        self.next_session_id += 1

        return session

    def get_by_id(self, session_id):
        return self.sessions.get(session_id)

    def get_question_by_id(self, question_id):
        for questions in self.questions.values():
            for question in questions:
                if question.id == question_id:
                    return question
        return None

    def list_questions_by_session_id(self, session_id):
        return sorted(
            self.questions.get(session_id, []),
            key=lambda item: (item.question_order, item.id),
        )

    def list_answered_question_ids_by_session_id(self, session_id):
        return {
            answer.question_id
            for answer in self.answers.get(session_id, [])
        }

    def get_next_unanswered_question(self, session_id):
        answered_question_ids = (
            self.list_answered_question_ids_by_session_id(
                session_id
            )
        )

        for question in self.list_questions_by_session_id(session_id):
            if question.id not in answered_question_ids:
                return question

        return None

    def create_answer(self, session_id, question, answer):
        item = SimpleNamespace(
            id=self.next_answer_id,
            session_id=session_id,
            question_id=question.id,
            question=question.question,
            answer=answer,
            question_category=question.question_category,
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

    def list_answers_by_session_id(self, session_id):
        return self.answers.get(session_id, [])


class FakeUserRepository:
    def get_by_id(self, user_id):
        return SimpleNamespace(id=user_id)


class FakeResumeRepository:
    def get_by_id(self, resume_id):
        return SimpleNamespace(id=resume_id, user_id=1)


class FakeJobRepository:
    def get_by_id(self, job_id):
        return SimpleNamespace(id=job_id)


@pytest.fixture
def repositories(monkeypatch):
    repository = FakeRepository()

    monkeypatch.setattr(
        service_module,
        "InterviewSessionRepository",
        lambda session: repository,
    )
    monkeypatch.setattr(
        service_module,
        "UserRepository",
        lambda session: FakeUserRepository(),
    )
    monkeypatch.setattr(
        service_module,
        "ResumeRepository",
        lambda session: FakeResumeRepository(),
    )
    monkeypatch.setattr(
        service_module,
        "JobRepository",
        lambda session: FakeJobRepository(),
    )
    monkeypatch.setattr(
        service_module,
        "build_interview_preparation",
        lambda **kwargs: InterviewPreparationResponse(
            resume_id=1,
            job_id=1,
            questions=[
                GeneratedQuestion(
                    question="First",
                    category="technical",
                    difficulty="medium",
                    priority="high",
                    reason="Required skill.",
                ),
                GeneratedQuestion(
                    question="Second",
                    category="behavioral",
                    difficulty="easy",
                    priority="low",
                    reason="Behavioral competency.",
                ),
            ],
        ),
    )

    return repository


def create_session(repositories):
    return InterviewSessionService(object()).create_session(
        InterviewSessionCreate(
            user_id=1,
            resume_id=1,
            job_id=1,
        )
    )


def test_session_creation_persists_questions(repositories):
    session = create_session(repositories)

    assert session.status == InterviewSessionStatus.ACTIVE
    assert [
        item.question
        for item in repositories.questions[session.id]
    ] == ["First", "Second"]


def test_list_questions_preserves_question_order(repositories):
    session = create_session(repositories)
    repositories.questions[session.id].reverse()

    result = InterviewSessionService(object()).list_questions(
        session.id
    )

    assert [item.question_order for item in result] == [1, 2]
    assert [item.question for item in result] == ["First", "Second"]


def test_list_questions_marks_unanswered_questions_false(
    repositories,
):
    session = create_session(repositories)

    result = InterviewSessionService(object()).list_questions(
        session.id
    )

    assert [item.answered for item in result] == [False, False]


def test_list_questions_marks_one_answered_question_true(
    repositories,
):
    session = create_session(repositories)
    first_question = repositories.questions[session.id][0]

    InterviewSessionService(object()).submit_answer(
        session.id,
        InterviewAnswerCreate(
            question_id=first_question.id,
            answer="Answer for the first question.",
        ),
    )

    result = InterviewSessionService(object()).list_questions(
        session.id
    )

    assert [item.answered for item in result] == [True, False]


def test_list_questions_marks_multiple_answered_questions_true(
    repositories,
):
    session = create_session(repositories)
    first_question = repositories.questions[session.id][0]
    second_question = repositories.questions[session.id][1]

    service = InterviewSessionService(object())
    service.submit_answer(
        session.id,
        InterviewAnswerCreate(
            question_id=first_question.id,
            answer="Answer for the first question.",
        ),
    )
    service.submit_answer(
        session.id,
        InterviewAnswerCreate(
            question_id=second_question.id,
            answer="Answer for the second question.",
        ),
    )

    result = service.list_questions(session.id)

    assert [item.answered for item in result] == [True, True]


def test_next_question_returns_first_unanswered_question(
    repositories,
):
    session = create_session(repositories)

    result = InterviewSessionService(object()).get_next_question(
        session.id
    )

    assert result.question == "First"
    assert result.question_order == 1
    assert result.answered is False


def test_next_question_skips_answered_first_question(
    repositories,
):
    session = create_session(repositories)
    first_question = repositories.questions[session.id][0]

    service = InterviewSessionService(object())
    service.submit_answer(
        session.id,
        InterviewAnswerCreate(
            question_id=first_question.id,
            answer="Answer for the first question.",
        ),
    )

    result = service.get_next_question(session.id)

    assert result.question == "Second"
    assert result.question_order == 2
    assert result.answered is False


def test_next_question_skips_multiple_answered_questions(
    repositories,
):
    session = create_session(repositories)
    repositories.questions[session.id].append(
        SimpleNamespace(
            id=3,
            session_id=session.id,
            question="Third",
            question_category="job_specific",
            difficulty="hard",
            priority="high",
            reason="Job-specific requirement.",
            question_order=3,
            created_at=datetime.now(timezone.utc),
        )
    )

    service = InterviewSessionService(object())
    service.submit_answer(
        session.id,
        InterviewAnswerCreate(
            question_id=1,
            answer="Answer one.",
        ),
    )
    service.submit_answer(
        session.id,
        InterviewAnswerCreate(
            question_id=2,
            answer="Answer two.",
        ),
    )

    result = service.get_next_question(session.id)

    assert result.question == "Third"
    assert result.question_order == 3
    assert result.answered is False


def test_next_question_uses_question_order_then_id(
    repositories,
):
    session = create_session(repositories)
    repositories.questions[session.id] = [
        SimpleNamespace(
            id=30,
            session_id=session.id,
            question="Later question",
            question_category="technical",
            difficulty="medium",
            priority="high",
            reason="Later order.",
            question_order=2,
            created_at=datetime.now(timezone.utc),
        ),
        SimpleNamespace(
            id=20,
            session_id=session.id,
            question="Tie second",
            question_category="technical",
            difficulty="medium",
            priority="high",
            reason="Tie order.",
            question_order=1,
            created_at=datetime.now(timezone.utc),
        ),
        SimpleNamespace(
            id=10,
            session_id=session.id,
            question="Tie first",
            question_category="technical",
            difficulty="medium",
            priority="high",
            reason="Tie order.",
            question_order=1,
            created_at=datetime.now(timezone.utc),
        ),
    ]

    result = InterviewSessionService(object()).get_next_question(
        session.id
    )

    assert result.id == 10
    assert result.question == "Tie first"


def test_next_question_rejects_all_answered_session(
    repositories,
):
    session = create_session(repositories)
    service = InterviewSessionService(object())

    for question in repositories.questions[session.id]:
        service.submit_answer(
            session.id,
            InterviewAnswerCreate(
                question_id=question.id,
                answer=f"Answer for question {question.id}.",
            ),
        )

    with pytest.raises(NoUnansweredInterviewQuestionError):
        service.get_next_question(session.id)


def test_next_question_rejects_session_with_zero_questions(
    repositories,
):
    session = create_session(repositories)
    repositories.questions[session.id] = []

    with pytest.raises(NoUnansweredInterviewQuestionError):
        InterviewSessionService(object()).get_next_question(session.id)


def test_next_question_rejects_missing_session(repositories):
    with pytest.raises(InterviewSessionNotFoundError):
        InterviewSessionService(object()).get_next_question(999)


def test_next_question_ignores_answers_from_other_sessions(
    repositories,
):
    first_session = create_session(repositories)
    second_session = create_session(repositories)
    second_question = repositories.questions[second_session.id][0]

    InterviewSessionService(object()).submit_answer(
        second_session.id,
        InterviewAnswerCreate(
            question_id=second_question.id,
            answer="Answer in a different session.",
        ),
    )

    result = InterviewSessionService(object()).get_next_question(
        first_session.id
    )

    assert result.session_id == first_session.id
    assert result.question == "First"
    assert result.answered is False


def test_missing_session_rejected_when_listing_questions(
    repositories,
):
    with pytest.raises(InterviewSessionNotFoundError):
        InterviewSessionService(object()).list_questions(999)


def test_answer_is_linked_to_persisted_question(repositories):
    session = create_session(repositories)

    answer = InterviewSessionService(object()).submit_answer(
        session.id,
        InterviewAnswerCreate(
            question_id=1,
            answer="A persisted-question answer.",
        ),
    )

    assert answer.question_id == 1
    assert answer.question == "First"
    assert answer.question_category == "technical"


def test_question_from_another_session_is_rejected(repositories):
    first_session = create_session(repositories)
    second_session = create_session(repositories)

    with pytest.raises(InterviewQuestionOwnershipError):
        InterviewSessionService(object()).submit_answer(
            second_session.id,
            InterviewAnswerCreate(
                question_id=repositories.questions[first_session.id][0].id,
                answer="Invalid cross-session answer.",
            ),
        )


def test_missing_question_is_rejected(repositories):
    session = create_session(repositories)

    with pytest.raises(InterviewQuestionNotFoundError):
        InterviewSessionService(object()).submit_answer(
            session.id,
            InterviewAnswerCreate(
                question_id=999,
                answer="Answer.",
            ),
        )


def test_question_relationship_has_cascade_delete():
    from app.models.interview_session import (
        InterviewQuestion,
        InterviewSession,
    )

    assert "delete-orphan" in InterviewSession.questions.property.cascade
    assert "delete-orphan" in InterviewQuestion.answers.property.cascade
    assert InterviewQuestion.answers.property.back_populates == (
        "question_record"
    )


def test_report_distinguishes_persisted_and_answered_questions(
    monkeypatch,
):
    from app.models.interview_report import InterviewSessionReport

    session = SimpleNamespace(id=1)
    questions = [
        SimpleNamespace(question_order=1),
        SimpleNamespace(question_order=2),
        SimpleNamespace(question_order=3),
    ]
    answers = [
        SimpleNamespace(
            id=10,
            session_id=1,
            question_category="technical",
        ),
    ]

    class ReportRepository:
        def __init__(self, session):
            pass

        def get_by_id(self, session_id):
            return session

        def list_questions_by_session_id(self, session_id):
            return questions

        def list_answers_by_session_id(self, session_id):
            return answers

    monkeypatch.setattr(
        interview_report_service,
        "InterviewSessionRepository",
        ReportRepository,
    )
    monkeypatch.setattr(
        interview_report_service,
        "evaluate_answer",
        lambda **kwargs: InterviewEvaluationResponse(
            session_id=1,
            answer_id=10,
            relevance_score=80.0,
            completeness_score=60.0,
            technical_score=100.0,
            overall_score=82.0,
            strengths=[],
            improvements=[],
        ),
    )

    result = interview_report_service.generate_interview_session_report(
        session_id=1,
        session=object(),
    )

    assert isinstance(result, InterviewSessionReport)
    assert result.total_questions == 3
    assert result.answered_questions == 1
    assert result.average_relevance_score == pytest.approx(80.0)
    assert result.average_completeness_score == pytest.approx(60.0)
    assert result.average_technical_score == pytest.approx(100.0)
    assert result.overall_score == pytest.approx(82.0)