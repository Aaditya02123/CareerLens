from types import SimpleNamespace

import pytest

from app.models.interview_evaluation import InterviewEvaluationResponse
from app.services import interview_evaluation_service as service_module
from app.services.interview_evaluation_service import (
    InterviewAnswerNotFoundError,
    InterviewSessionNotFoundError,
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
    ResumeNotFoundError,
)


class FakeInterviewSessionRepository:
    def __init__(self, interview_session=None, answers=None):
        self.interview_session = interview_session
        self.answers = answers or []

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


class FakeResumeRepository:
    def __init__(self, resume=None):
        self.resume = resume

    def get_by_id(self, resume_id: int):
        if self.resume is not None and self.resume.id == resume_id:
            return self.resume
        return None


class FakeJobRepository:
    def __init__(self, job=None):
        self.job = job

    def get_by_id(self, job_id: int):
        if self.job is not None and self.job.id == job_id:
            return self.job
        return None


class FakeResumeAnalysisRepository:
    def __init__(self, analysis=None):
        self.analysis = analysis

    def get_by_resume_id(self, resume_id: int):
        if (
            self.analysis is not None
            and self.analysis.resume_id == resume_id
        ):
            return self.analysis
        return None


@pytest.fixture
def evaluation_context(monkeypatch):
    interview_session = SimpleNamespace(
        id=1,
        resume_id=10,
        job_id=20,
    )
    answer = SimpleNamespace(
        id=100,
        session_id=1,
        question="Explain Python APIs",
        answer="Python APIs are useful for building services.",
        question_category="technical",
    )
    resume = SimpleNamespace(id=10)
    job = SimpleNamespace(
        id=20,
        required_skills=["Python", "FastAPI", "PostgreSQL"],
    )
    analysis = SimpleNamespace(
        resume_id=10,
        structured_resume={
            "name": "Test User",
            "email": "test@example.com",
            "skills": ["Python"],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
        },
        categorized_skills={"skills": []},
    )

    repositories = {
        "sessions": FakeInterviewSessionRepository(
            interview_session=interview_session,
            answers=[answer],
        ),
        "resumes": FakeResumeRepository(resume=resume),
        "jobs": FakeJobRepository(job=job),
        "analyses": FakeResumeAnalysisRepository(analysis=analysis),
    }

    monkeypatch.setattr(
        service_module,
        "InterviewSessionRepository",
        lambda session: repositories["sessions"],
    )
    monkeypatch.setattr(
        service_module,
        "ResumeRepository",
        lambda session: repositories["resumes"],
    )
    monkeypatch.setattr(
        service_module,
        "JobRepository",
        lambda session: repositories["jobs"],
    )
    monkeypatch.setattr(
        service_module,
        "ResumeAnalysisRepository",
        lambda session: repositories["analyses"],
    )

    return {
        "session": interview_session,
        "answer": answer,
        "resume": resume,
        "job": job,
        "analysis": analysis,
        "repositories": repositories,
    }


def test_relevance_score_uses_meaningful_question_token_overlap():
    score = service_module._score_relevance(
        question="Explain Python APIs",
        answer="Python APIs are useful for building services.",
    )

    assert score == pytest.approx(66.6666666667)


def test_relevance_score_is_zero_when_question_has_no_meaningful_tokens():
    score = service_module._score_relevance(
        question="How are you?",
        answer="I am ready.",
    )

    assert score == 0.0


@pytest.mark.parametrize(
    ("answer", "expected_score"),
    [
        ("", 0.0),
        ("one two three", 25.0),
        (" ".join(["word"] * 15), 50.0),
        (" ".join(["word"] * 40), 75.0),
        (" ".join(["word"] * 80), 100.0),
    ],
)
def test_completeness_score_uses_word_count_thresholds(
    answer,
    expected_score,
):
    assert service_module._score_completeness(answer) == expected_score


def test_technical_score_counts_two_of_three_required_skills():
    score = service_module._score_technical(
        answer="I used Python and FastAPI to build the service.",
        question_category="technical",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        resume=SimpleNamespace(),
    )

    assert score == pytest.approx(66.6666666667)


def test_technical_score_is_one_hundred_when_all_skills_are_mentioned():
    score = service_module._score_technical(
        answer="I used Python, FastAPI, and PostgreSQL.",
        question_category="technical",
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        resume=SimpleNamespace(),
    )

    assert score == 100.0


def test_technical_score_is_case_insensitive():
    score = service_module._score_technical(
        answer="I used python and FASTAPI.",
        question_category="technical",
        required_skills=["Python", "FastAPI"],
        resume=SimpleNamespace(),
    )

    assert score == 100.0


def test_technical_score_is_zero_without_required_skills():
    score = service_module._score_technical(
        answer="I have experience with Python and FastAPI.",
        question_category="technical",
        required_skills=[],
        resume=SimpleNamespace(),
    )

    assert score == 0.0


@pytest.mark.parametrize(
    "question_category",
    ["resume_based", "behavioral"],
)
def test_technical_score_is_zero_for_non_technical_categories(
    question_category,
):
    score = service_module._score_technical(
        answer="Python FastAPI PostgreSQL",
        question_category=question_category,
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        resume=SimpleNamespace(),
    )

    assert score == 0.0


def test_overall_score_uses_technical_weighted_formula():
    score = service_module._overall_score(
        relevance_score=80.0,
        completeness_score=60.0,
        technical_score=50.0,
        question_category="technical",
    )

    expected = (
        80.0 * 0.35
        + 60.0 * 0.25
        + 50.0 * 0.40
    )

    assert score == pytest.approx(expected)


def test_overall_score_uses_non_technical_weighted_formula():
    score = service_module._overall_score(
        relevance_score=80.0,
        completeness_score=60.0,
        technical_score=0.0,
        question_category="behavioral",
    )

    expected = 80.0 * 0.55 + 60.0 * 0.45

    assert score == pytest.approx(expected)


def test_high_relevance_adds_relevance_strength():
    strengths, improvements = service_module._build_feedback(
        relevance_score=80.0,
        completeness_score=75.0,
        technical_score=80.0,
        overall_score=80.0,
        question_category="technical",
    )

    assert "The answer addresses the question directly." in strengths
    assert "Connect the answer more directly to the question." not in (
        improvements
    )


def test_low_relevance_adds_relevance_improvement():
    strengths, improvements = service_module._build_feedback(
        relevance_score=40.0,
        completeness_score=75.0,
        technical_score=80.0,
        overall_score=60.0,
        question_category="technical",
    )

    assert "Connect the answer more directly to the question." in (
        improvements
    )


def test_high_completeness_adds_completeness_strength():
    strengths, improvements = service_module._build_feedback(
        relevance_score=80.0,
        completeness_score=75.0,
        technical_score=80.0,
        overall_score=80.0,
        question_category="technical",
    )

    assert "The answer provides useful detail." in strengths


def test_low_completeness_adds_completeness_improvement():
    strengths, improvements = service_module._build_feedback(
        relevance_score=80.0,
        completeness_score=50.0,
        technical_score=80.0,
        overall_score=60.0,
        question_category="technical",
    )

    assert "Add more specific detail, examples, or explanation." in (
        improvements
    )


def test_high_technical_score_adds_technical_strength():
    strengths, improvements = service_module._build_feedback(
        relevance_score=80.0,
        completeness_score=75.0,
        technical_score=80.0,
        overall_score=80.0,
        question_category="technical",
    )

    assert (
        "The answer references relevant technical requirements."
        in strengths
    )


def test_low_technical_score_adds_technical_improvement():
    strengths, improvements = service_module._build_feedback(
        relevance_score=80.0,
        completeness_score=75.0,
        technical_score=40.0,
        overall_score=60.0,
        question_category="technical",
    )

    assert (
        "Address more of the technical requirements in the answer."
        in improvements
    )


def test_high_overall_score_adds_baseline_response_strength():
    strengths, improvements = service_module._build_feedback(
        relevance_score=80.0,
        completeness_score=75.0,
        technical_score=80.0,
        overall_score=70.0,
        question_category="technical",
    )

    assert (
        "The answer demonstrates a strong baseline response structure."
        in strengths
    )


def test_feedback_has_fallback_strength_when_no_other_strength_applies():
    strengths, improvements = service_module._build_feedback(
        relevance_score=0.0,
        completeness_score=0.0,
        technical_score=0.0,
        overall_score=0.0,
        question_category="behavioral",
    )

    assert strengths == ["The answer contains a submitted response."]


def test_evaluate_answer_rejects_missing_session(
    evaluation_context,
):
    repositories = evaluation_context["repositories"]
    repositories["sessions"].interview_session = None

    with pytest.raises(InterviewSessionNotFoundError):
        service_module.evaluate_answer(
            session_id=1,
            answer_id=100,
            session=object(),
        )


def test_evaluate_answer_rejects_missing_answer_for_session(
    evaluation_context,
):
    repositories = evaluation_context["repositories"]
    repositories["sessions"].answers = []

    with pytest.raises(InterviewAnswerNotFoundError):
        service_module.evaluate_answer(
            session_id=1,
            answer_id=100,
            session=object(),
        )


def test_evaluate_answer_rejects_answer_belonging_to_another_session(
    evaluation_context,
):
    repositories = evaluation_context["repositories"]
    repositories["sessions"].answers = [
        SimpleNamespace(
            id=100,
            session_id=2,
            question="Explain Python APIs",
            answer="Python APIs are useful.",
            question_category="technical",
        )
    ]

    with pytest.raises(InterviewAnswerNotFoundError):
        service_module.evaluate_answer(
            session_id=1,
            answer_id=100,
            session=object(),
        )


def test_evaluate_answer_rejects_missing_resume(evaluation_context):
    repositories = evaluation_context["repositories"]
    repositories["resumes"].resume = None

    with pytest.raises(ResumeNotFoundError):
        service_module.evaluate_answer(
            session_id=1,
            answer_id=100,
            session=object(),
        )


def test_evaluate_answer_rejects_missing_job(evaluation_context):
    repositories = evaluation_context["repositories"]
    repositories["jobs"].job = None

    with pytest.raises(JobNotFoundError):
        service_module.evaluate_answer(
            session_id=1,
            answer_id=100,
            session=object(),
        )


def test_evaluate_answer_rejects_missing_resume_analysis(
    evaluation_context,
):
    repositories = evaluation_context["repositories"]
    repositories["analyses"].analysis = None

    with pytest.raises(ResumeAnalysisNotFoundError):
        service_module.evaluate_answer(
            session_id=1,
            answer_id=100,
            session=object(),
        )


def test_evaluate_answer_returns_structured_response(evaluation_context):
    result = service_module.evaluate_answer(
        session_id=1,
        answer_id=100,
        session=object(),
    )

    assert isinstance(result, InterviewEvaluationResponse)
    assert result.session_id == 1
    assert result.answer_id == 100
    assert 0.0 <= result.relevance_score <= 100.0
    assert 0.0 <= result.completeness_score <= 100.0
    assert 0.0 <= result.technical_score <= 100.0
    assert 0.0 <= result.overall_score <= 100.0