from collections.abc import Generator
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import interview_sessions as api_module
from app.core.database import get_db
from app.main import app
from app.models.interview_session import (
    InterviewQuestionResponse,
    InterviewSessionStatus,
)
from app.services.interview_session_service import (
    DuplicateInterviewAnswerError,
    InactiveInterviewSessionError,
    InterviewQuestionNotFoundError,
    InterviewQuestionOwnershipError,
    InterviewSessionNotFoundError,
    InvalidInterviewSessionStatusTransitionError,
    NoUnansweredInterviewQuestionError,
)


def make_session_response(session_id, status):
    return SimpleNamespace(
        id=session_id,
        user_id=1,
        resume_id=1,
        job_id=1,
        status=status,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        answers=[],
    )


class FakeService:
    def __init__(self, session):
        pass

    def list_questions(self, session_id):
        if session_id == 999:
            raise InterviewSessionNotFoundError("Session not found.")

        return [
            InterviewQuestionResponse(
                id=2,
                session_id=session_id,
                question="Second persisted question",
                question_category="behavioral",
                difficulty="easy",
                priority="low",
                reason="Behavioral competency.",
                question_order=2,
                created_at=datetime.now(timezone.utc),
                answered=False,
            ),
            InterviewQuestionResponse(
                id=1,
                session_id=session_id,
                question="First persisted question",
                question_category="technical",
                difficulty="medium",
                priority="high",
                reason="Required skill.",
                question_order=1,
                created_at=datetime.now(timezone.utc),
                answered=True,
            ),
        ]

    def get_next_question(self, session_id):
        if session_id == 999:
            raise InterviewSessionNotFoundError("Session not found.")

        if session_id == 888:
            raise NoUnansweredInterviewQuestionError(
                "No unanswered interview questions remain."
            )

        return InterviewQuestionResponse(
            id=3,
            session_id=session_id,
            question="Next unanswered question",
            question_category="technical",
            difficulty="medium",
            priority="high",
            reason="Required skill.",
            question_order=3,
            created_at=datetime.now(timezone.utc),
            answered=False,
        )

    def update_session_status(self, session_id, new_status):
        if session_id == 999:
            raise InterviewSessionNotFoundError("Session not found.")

        if session_id == 10 and new_status == (
            InterviewSessionStatus.ACTIVE
        ):
            raise InvalidInterviewSessionStatusTransitionError(
                "Interview session is already completed and cannot "
                "transition to active."
            )

        if session_id == 11 and new_status == (
            InterviewSessionStatus.ABANDONED
        ):
            raise InvalidInterviewSessionStatusTransitionError(
                "Interview session is already completed and cannot "
                "transition to abandoned."
            )

        if session_id == 20 and new_status == (
            InterviewSessionStatus.ACTIVE
        ):
            raise InvalidInterviewSessionStatusTransitionError(
                "Interview session is already abandoned and cannot "
                "transition to active."
            )

        if session_id == 21 and new_status == (
            InterviewSessionStatus.COMPLETED
        ):
            raise InvalidInterviewSessionStatusTransitionError(
                "Interview session is already abandoned and cannot "
                "transition to completed."
            )

        return make_session_response(
            session_id=session_id,
            status=new_status,
        )

    def submit_answer(self, session_id, answer_data):
        if answer_data.question_id == 999:
            raise InterviewQuestionNotFoundError("Question not found.")

        if answer_data.question_id == 200:
            raise InterviewQuestionOwnershipError(
                "The question does not belong to this session."
            )

        if answer_data.question_id == 300:
            raise InactiveInterviewSessionError(
                "Answers can only be submitted to an active session."
            )

        if answer_data.question_id == 400:
            raise DuplicateInterviewAnswerError(
                "This interview question already has an answer."
            )

        return SimpleNamespace(
            id=1,
            session_id=session_id,
            question_id=answer_data.question_id,
            question="Persisted question",
            answer=answer_data.answer,
            question_category="technical",
            created_at=datetime.now(timezone.utc),
        )


@pytest.fixture
def client(monkeypatch) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: object()
    monkeypatch.setattr(
        api_module,
        "InterviewSessionService",
        FakeService,
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_list_questions_returns_answered_flags(client):
    response = client.get("/interview-sessions/1/questions")

    assert response.status_code == 200
    body = response.json()

    assert body[0]["answered"] is False
    assert body[1]["answered"] is True


def test_list_questions_preserves_service_response_order(client):
    response = client.get("/interview-sessions/1/questions")

    assert response.status_code == 200
    assert [item["question_order"] for item in response.json()] == [
        2,
        1,
    ]


def test_list_questions_missing_session_returns_404(client):
    response = client.get("/interview-sessions/999/questions")

    assert response.status_code == 404


def test_next_question_returns_200_with_unanswered_question(client):
    response = client.get("/interview-sessions/1/next-question")

    assert response.status_code == 200
    body = response.json()

    assert body["question"] == "Next unanswered question"
    assert body["question_order"] == 3
    assert body["answered"] is False


def test_next_question_all_answered_returns_404(client):
    response = client.get("/interview-sessions/888/next-question")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "No unanswered interview questions remain."
    )


def test_next_question_missing_session_returns_404(client):
    response = client.get("/interview-sessions/999/next-question")

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("session_id", "new_status"),
    [
        (1, "completed"),
        (2, "abandoned"),
    ],
)
def test_status_update_from_active_returns_success(
    client,
    session_id,
    new_status,
):
    response = client.patch(
        f"/interview-sessions/{session_id}/status",
        json={"status": new_status},
    )

    assert response.status_code == 200
    assert response.json()["status"] == new_status


@pytest.mark.parametrize(
    ("session_id", "new_status", "message"),
    [
        (
            10,
            "active",
            "Interview session is already completed and cannot "
            "transition to active.",
        ),
        (
            11,
            "abandoned",
            "Interview session is already completed and cannot "
            "transition to abandoned.",
        ),
        (
            20,
            "active",
            "Interview session is already abandoned and cannot "
            "transition to active.",
        ),
        (
            21,
            "completed",
            "Interview session is already abandoned and cannot "
            "transition to completed.",
        ),
    ],
)
def test_terminal_status_update_returns_400(
    client,
    session_id,
    new_status,
    message,
):
    response = client.patch(
        f"/interview-sessions/{session_id}/status",
        json={"status": new_status},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == message


def test_status_update_missing_session_returns_404(client):
    response = client.patch(
        "/interview-sessions/999/status",
        json={"status": "completed"},
    )

    assert response.status_code == 404


def test_first_answer_returns_201(client):
    response = client.post(
        "/interview-sessions/1/answers",
        json={
            "question_id": 100,
            "answer": "First answer.",
        },
    )

    assert response.status_code == 201


def test_answer_response_contains_persisted_question_details(client):
    response = client.post(
        "/interview-sessions/1/answers",
        json={
            "question_id": 100,
            "answer": "First answer.",
        },
    )

    assert response.status_code == 201
    body = response.json()

    assert body["question_id"] == 100
    assert body["question"] == "Persisted question"
    assert body["question_category"] == "technical"


def test_duplicate_answer_returns_409(client):
    response = client.post(
        "/interview-sessions/1/answers",
        json={
            "question_id": 400,
            "answer": "Duplicate answer.",
        },
    )

    assert response.status_code == 409


@pytest.mark.parametrize(
    ("question_id", "expected_status"),
    [
        (999, 404),
        (200, 400),
        (300, 400),
    ],
)
def test_answer_errors_preserve_existing_http_mapping(
    client,
    question_id,
    expected_status,
):
    response = client.post(
        "/interview-sessions/1/answers",
        json={
            "question_id": question_id,
            "answer": "Answer.",
        },
    )

    assert response.status_code == expected_status