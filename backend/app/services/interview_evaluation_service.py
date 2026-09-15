import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.interview_evaluation import InterviewEvaluationResponse
from app.models.resume import StructuredResume
from app.models.resume_analysis import ResumeAnalysis
from app.repositories.interview_session_repository import (
    InterviewSessionRepository,
)
from app.repositories.job_repository import JobRepository
from app.repositories.resume_analysis_repository import (
    ResumeAnalysisRepository,
)
from app.repositories.resume_repository import ResumeRepository
from app.services.llm.interview_evaluator import InterviewEvaluator
from app.services.llm.providers import (
    OpenAICompatibleInterviewProvider,
)


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "use",
    "what",
    "would",
    "you",
}

TECHNICAL_CATEGORIES = {
    "technical",
    "job_specific",
}


class InterviewSessionNotFoundError(LookupError):
    """Raised when an interview session does not exist."""


class InterviewAnswerNotFoundError(LookupError):
    """Raised when an answer does not exist for a session."""


class ResumeAnalysisNotFoundError(LookupError):
    """Raised when persisted resume analysis does not exist."""


class ResumeNotFoundError(LookupError):
    """Raised when a session's resume does not exist."""


class JobNotFoundError(LookupError):
    """Raised when a session's job does not exist."""


def _tokens(text: str) -> set[str]:
    """Return meaningful lowercase word tokens."""
    return {
        token
        for token in re.findall(r"[a-z0-9+#.]+", text.casefold())
        if token not in STOPWORDS
    }


def _score_relevance(question: str, answer: str) -> float:
    """Score overlap between the question and answer text."""
    question_tokens = _tokens(question)
    answer_tokens = _tokens(answer)

    if not question_tokens:
        return 0.0

    return (
        len(question_tokens & answer_tokens)
        / len(question_tokens)
        * 100.0
    )


def _score_completeness(answer: str) -> float:
    """Score answer detail using deterministic word-count thresholds."""
    word_count = len(answer.split())

    if word_count >= 80:
        return 100.0

    if word_count >= 40:
        return 75.0

    if word_count >= 15:
        return 50.0

    return 25.0 if word_count > 0 else 0.0


def _score_technical(
    answer: str,
    question_category: str,
    required_skills: list[str],
    resume: StructuredResume,
) -> float:
    """Score technical coverage against explicit job requirements."""
    if question_category not in TECHNICAL_CATEGORIES:
        return 0.0

    if not required_skills:
        return 0.0

    answer_text = answer.casefold()
    skills = [
        skill.strip()
        for skill in required_skills
        if skill.strip()
    ]

    if not skills:
        return 0.0

    matched_count = sum(
        1
        for skill in skills
        if skill.casefold() in answer_text
    )

    return matched_count / len(skills) * 100.0


def _overall_score(
    relevance_score: float,
    completeness_score: float,
    technical_score: float,
    question_category: str,
) -> float:
    """Combine explainable component scores."""
    if question_category in TECHNICAL_CATEGORIES:
        return (
            relevance_score * 0.35
            + completeness_score * 0.25
            + technical_score * 0.40
        )

    return relevance_score * 0.55 + completeness_score * 0.45


def _build_feedback(
    relevance_score: float,
    completeness_score: float,
    technical_score: float,
    overall_score: float,
    question_category: str,
) -> tuple[list[str], list[str]]:
    """Generate deterministic strengths and improvements."""
    strengths: list[str] = []
    improvements: list[str] = []

    if relevance_score >= 70.0:
        strengths.append("The answer addresses the question directly.")
    else:
        improvements.append(
            "Connect the answer more directly to the question."
        )

    if completeness_score >= 75.0:
        strengths.append("The answer provides useful detail.")
    else:
        improvements.append(
            "Add more specific detail, examples, or explanation."
        )

    if question_category in TECHNICAL_CATEGORIES:
        if technical_score >= 70.0:
            strengths.append(
                "The answer references relevant technical requirements."
            )
        else:
            improvements.append(
                "Address more of the technical requirements in the answer."
            )

    if overall_score >= 70.0:
        strengths.append(
            "The answer demonstrates a strong baseline response structure."
        )

    if not strengths:
        strengths.append("The answer contains a submitted response.")

    return strengths, improvements


def _get_answer_for_session(
    repository: InterviewSessionRepository,
    session_id: int,
    answer_id: int,
):
    """Find an answer and ensure it belongs to the requested session."""
    answers = repository.list_answers_by_session_id(session_id)

    for answer in answers:
        if answer.id == answer_id:
            return answer

    raise InterviewAnswerNotFoundError(
        "The requested answer was not found for this session."
    )


def evaluate_answer(
    session_id: int,
    answer_id: int,
    session: Session,
) -> InterviewEvaluationResponse:
    """Evaluate a submitted interview answer deterministically."""
    session_repository = InterviewSessionRepository(session)
    interview_session = session_repository.get_by_id(session_id)

    if interview_session is None:
        raise InterviewSessionNotFoundError(
            "The requested interview session was not found."
        )

    answer = _get_answer_for_session(
        repository=session_repository,
        session_id=session_id,
        answer_id=answer_id,
    )

    resume_repository = ResumeRepository(session)
    resume = resume_repository.get_by_id(interview_session.resume_id)

    if resume is None:
        raise ResumeNotFoundError(
            "The session's resume was not found."
        )

    job_repository = JobRepository(session)
    job = job_repository.get_by_id(interview_session.job_id)

    if job is None:
        raise JobNotFoundError(
            "The session's job was not found."
        )

    analysis_repository = ResumeAnalysisRepository(session)
    analysis = analysis_repository.get_by_resume_id(resume.id)

    if analysis is None:
        raise ResumeAnalysisNotFoundError(
            "No persisted resume analysis was found."
        )

    structured_resume = StructuredResume.model_validate(
        analysis.structured_resume
    )

    relevance_score = _score_relevance(
        question=answer.question,
        answer=answer.answer,
    )
    completeness_score = _score_completeness(answer.answer)
    technical_score = _score_technical(
        answer=answer.answer,
        question_category=answer.question_category,
        required_skills=job.required_skills,
        resume=structured_resume,
    )
    overall_score = _overall_score(
        relevance_score=relevance_score,
        completeness_score=completeness_score,
        technical_score=technical_score,
        question_category=answer.question_category,
    )

    strengths, improvements = _build_feedback(
        relevance_score=relevance_score,
        completeness_score=completeness_score,
        technical_score=technical_score,
        overall_score=overall_score,
        question_category=answer.question_category,
    )

    return InterviewEvaluationResponse(
        session_id=session_id,
        answer_id=answer_id,
        relevance_score=relevance_score,
        completeness_score=completeness_score,
        technical_score=technical_score,
        overall_score=overall_score,
        strengths=strengths,
        improvements=improvements,
    )


def evaluate_answer_with_llm(
    session_id: int,
    answer_id: int,
    session: Session,
    evaluator: InterviewEvaluator | None = None,
) -> InterviewEvaluationResponse:
    """Evaluate an answer through the separate LLM evaluation path."""
    session_repository = InterviewSessionRepository(session)
    interview_session = session_repository.get_by_id(session_id)

    if interview_session is None:
        raise InterviewSessionNotFoundError(
            "The requested interview session was not found."
        )

    answer = _get_answer_for_session(
        repository=session_repository,
        session_id=session_id,
        answer_id=answer_id,
    )

    resume = ResumeRepository(session).get_by_id(
        interview_session.resume_id
    )
    if resume is None:
        raise ResumeNotFoundError(
            "The session's resume was not found."
        )

    job = JobRepository(session).get_by_id(
        interview_session.job_id
    )
    if job is None:
        raise JobNotFoundError(
            "The session's job was not found."
        )

    analysis = ResumeAnalysisRepository(session).get_by_resume_id(
        resume.id
    )
    if analysis is None:
        raise ResumeAnalysisNotFoundError(
            "No persisted resume analysis was found."
        )

    structured_resume = StructuredResume.model_validate(
        analysis.structured_resume
    )

    context: dict[str, Any] = {
        "question": answer.question,
        "answer": answer.answer,
        "question_category": answer.question_category,
        "job": {
            "title": job.title,
            "description": job.description,
            "required_skills": job.required_skills,
        },
        "structured_resume": structured_resume.model_dump(
            mode="json"
        ),
    }

    active_evaluator = evaluator or InterviewEvaluator(
        provider=OpenAICompatibleInterviewProvider()
    )
    result = active_evaluator.evaluate(context)

    return InterviewEvaluationResponse(
        session_id=session_id,
        answer_id=answer_id,
        relevance_score=result.relevance_score,
        completeness_score=result.completeness_score,
        technical_score=result.technical_score,
        overall_score=result.overall_score,
        strengths=result.strengths,
        improvements=result.improvements,
    )