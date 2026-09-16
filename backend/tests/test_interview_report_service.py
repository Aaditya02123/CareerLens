from types import SimpleNamespace

import pytest

from app.models.interview_evaluation import InterviewEvaluationResponse
from app.services import interview_evaluation_service
from app.services import interview_report_service as service_module
from app.services.interview_evaluation_service import (
    InterviewSessionNotFoundError,
)


class FakeInterviewSessionRepository:
    def __init__(self, interview_session=None, answers=None, questions=None):
        self.interview_session = interview_session
        self.answers = answers or []
        self.questions = questions or []

    def get_by_id(self, session_id: int):
        if (
            self.interview_session is not None
            and self.interview_session.id == session_id
        ):
            return self.interview_session

        return None

    def list_answers_by_session_id(self, session_id: int):
        return [
            answer
            for answer in self.answers
            if answer.session_id == session_id
        ]
    def list_questions_by_session_id(self, session_id : int):
        return[
            question
            for question in self.questions
            if question.session_id == session_id
        ]


def make_answer(
    answer_id: int,
    category: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=answer_id,
        session_id=1,
        question=f"Question {answer_id}",
        answer=f"Answer {answer_id}",
        question_category=category,
    )
def make_question(
    question_id: int,
    question_order: int,
    category: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=question_id,
        session_id=1,
        question=f"Question {question_id}",
        question_category=category,
        difficulty="medium",
        priority="medium",
        reason="Test question.",
        question_order=question_order,
    )

def make_evaluation(
    answer_id: int,
    relevance: float,
    completeness: float,
    technical: float,
    overall: float,
    strengths: list[str] | None = None,
    improvements: list[str] | None = None,
) -> InterviewEvaluationResponse:
    return InterviewEvaluationResponse(
        session_id=1,
        answer_id=answer_id,
        relevance_score=relevance,
        completeness_score=completeness,
        technical_score=technical,
        overall_score=overall,
        strengths=strengths or [],
        improvements=improvements or [],
    )


@pytest.fixture
def report_context(monkeypatch):
    interview_session = SimpleNamespace(id=1)
    answers = [
        make_answer(101, "technical"),
        make_answer(102, "behavioral"),
    ]
    repository = FakeInterviewSessionRepository(
        interview_session=interview_session,
        answers=answers,
        questions=[
            make_question(101,1,"technical"),
            make_question(102,2,"behavioral"),
        ],
    )

    monkeypatch.setattr(
        service_module,
        "InterviewSessionRepository",
        lambda session: repository,
    )

    return repository


def test_missing_session_raises_error(monkeypatch):
    repository = FakeInterviewSessionRepository(
        interview_session=None,
    )

    monkeypatch.setattr(
        service_module,
        "InterviewSessionRepository",
        lambda session: repository,
    )

    with pytest.raises(InterviewSessionNotFoundError):
        service_module.generate_interview_session_report(
            session_id=1,
            session=object(),
        )


def test_zero_answers_returns_zero_scores_and_empty_feedback(
    monkeypatch,
):
    repository = FakeInterviewSessionRepository(
        interview_session=SimpleNamespace(id=1),
        answers=[],
    )

    monkeypatch.setattr(
        service_module,
        "InterviewSessionRepository",
        lambda session: repository,
    )

    result = service_module.generate_interview_session_report(
        session_id=1,
        session=object(),
    )

    assert result.total_questions == 0
    assert result.answered_questions == 0
    assert result.average_relevance_score == 0.0
    assert result.average_completeness_score == 0.0
    assert result.average_technical_score == 0.0
    assert result.overall_score == 0.0
    assert result.strengths == []
    assert result.improvements == []

    for category_score in result.category_scores.values():
        assert category_score.average_overall_score == 0.0
        assert category_score.answer_count == 0


def test_one_answer_is_evaluated_and_aggregated(
    report_context,
    monkeypatch,
):
    evaluation = make_evaluation(
        answer_id=101,
        relevance=80.0,
        completeness=60.0,
        technical=100.0,
        overall=82.0,
        strengths=["Strong technical explanation."],
        improvements=["Add an example."],
    )
    calls = []

    def fake_evaluate_answer(**kwargs):
        calls.append(kwargs)
        return evaluation

    monkeypatch.setattr(
        service_module,
        "evaluate_answer",
        fake_evaluate_answer,
    )
    report_context.answers = [make_answer(101, "technical")]

    result = service_module.generate_interview_session_report(
        session_id=1,
        session=object(),
    )

    assert len(calls) == 1
    assert calls[0]["session_id"] == 1
    assert calls[0]["answer_id"] == 101
    assert result.total_questions == 2
    assert result.answered_questions == 1
    assert result.average_relevance_score == 80.0
    assert result.average_completeness_score == 60.0
    assert result.average_technical_score == 100.0
    assert result.overall_score == 82.0
    assert result.category_scores["technical"].answer_count == 1
    assert (
        result.category_scores["technical"].average_overall_score
        == 82.0
    )


def test_multiple_answers_use_arithmetic_means_and_categories(
    report_context,
    monkeypatch,
):
    evaluations = {
        101: make_evaluation(
            answer_id=101,
            relevance=80.0,
            completeness=60.0,
            technical=100.0,
            overall=82.0,
            strengths=["Clear explanation."],
            improvements=["Add an example."],
        ),
        102: make_evaluation(
            answer_id=102,
            relevance=60.0,
            completeness=40.0,
            technical=0.0,
            overall=51.0,
            strengths=["clear explanation."],
            improvements=["Use a concrete example."],
        ),
    }

    calls = []

    def fake_evaluate_answer(**kwargs):
        calls.append(kwargs["answer_id"])
        return evaluations[kwargs["answer_id"]]

    monkeypatch.setattr(
        service_module,
        "evaluate_answer",
        fake_evaluate_answer,
    )

    result = service_module.generate_interview_session_report(
        session_id=1,
        session=object(),
    )

    assert calls == [101, 102]
    assert result.total_questions == 2
    assert result.answered_questions == 2
    assert result.average_relevance_score == pytest.approx(70.0)
    assert result.average_completeness_score == pytest.approx(50.0)
    assert result.average_technical_score == pytest.approx(50.0)
    assert result.overall_score == pytest.approx(66.5)

    assert result.category_scores["technical"].answer_count == 1
    assert (
        result.category_scores["technical"].average_overall_score
        == pytest.approx(82.0)
    )
    assert result.category_scores["behavioral"].answer_count == 1
    assert (
        result.category_scores["behavioral"].average_overall_score
        == pytest.approx(51.0)
    )


def test_categories_without_answers_receive_zero(
    report_context,
    monkeypatch,
):
    answer = make_answer(101, "technical")
    report_context.answers = [answer]

    monkeypatch.setattr(
        service_module,
        "evaluate_answer",
        lambda **kwargs: make_evaluation(
            answer_id=101,
            relevance=70.0,
            completeness=70.0,
            technical=70.0,
            overall=70.0,
        ),
    )

    result = service_module.generate_interview_session_report(
        session_id=1,
        session=object(),
    )

    for category in (
        "resume_based",
        "behavioral",
        "job_specific",
    ):
        assert result.category_scores[category].answer_count == 0
        assert (
            result.category_scores[category].average_overall_score
            == 0.0
        )


def test_duplicate_feedback_is_removed_case_insensitively(
    report_context,
    monkeypatch,
):
    evaluations = {
        101: make_evaluation(
            answer_id=101,
            relevance=70.0,
            completeness=70.0,
            technical=70.0,
            overall=70.0,
            strengths=["Direct answer", "Useful detail"],
            improvements=["Add examples"],
        ),
        102: make_evaluation(
            answer_id=102,
            relevance=70.0,
            completeness=70.0,
            technical=0.0,
            overall=70.0,
            strengths=["direct answer", "Another strength"],
            improvements=["ADD EXAMPLES"],
        ),
    }

    monkeypatch.setattr(
        service_module,
        "evaluate_answer",
        lambda **kwargs: evaluations[kwargs["answer_id"]],
    )

    result = service_module.generate_interview_session_report(
        session_id=1,
        session=object(),
    )

    assert result.strengths == [
        "Direct answer",
        "Useful detail",
        "Another strength",
    ]
    assert result.improvements == ["Add examples"]


def test_each_answer_uses_deterministic_evaluator_and_not_llm(
    report_context,
    monkeypatch,
):
    calls = []

    def fake_deterministic_evaluator(**kwargs):
        calls.append(kwargs["answer_id"])
        return make_evaluation(
            answer_id=kwargs["answer_id"],
            relevance=50.0,
            completeness=50.0,
            technical=0.0,
            overall=50.0,
        )

    def fail_if_llm_is_called(*args, **kwargs):
        pytest.fail(
            "Interview reports must not call the LLM evaluator."
        )

    monkeypatch.setattr(
        service_module,
        "evaluate_answer",
        fake_deterministic_evaluator,
    )
    monkeypatch.setattr(
        interview_evaluation_service,
        "evaluate_answer_with_llm",
        fail_if_llm_is_called,
    )

    result = service_module.generate_interview_session_report(
        session_id=1,
        session=object(),
    )

    assert calls == [101, 102]
    assert result.answered_questions == 2