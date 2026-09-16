from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.models.interview_evaluation import InterviewEvaluationResponse
from app.models.interview_report import (
    InterviewCategoryScore,
    InterviewQuestionCategory,
    InterviewSessionReport,
)
from app.repositories.interview_session_repository import (
    InterviewSessionRepository,
)
from app.services.interview_evaluation_service import (
    InterviewSessionNotFoundError,
    evaluate_answer,
)


INTERVIEW_CATEGORIES: tuple[InterviewQuestionCategory, ...] = (
    "technical",
    "resume_based",
    "behavioral",
    "job_specific",
)


def _average(values: Iterable[float]) -> float:
    values_list = list(values)
    return sum(values_list) / len(values_list) if values_list else 0.0


def _unique_feedback(evaluations, field_name: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for evaluation in evaluations:
        for item in getattr(evaluation, field_name):
            key = item.casefold()
            if key not in seen:
                seen.add(key)
                result.append(item)

    return result


def generate_interview_session_report(
    session_id: int,
    session: Session,
) -> InterviewSessionReport:
    repository = InterviewSessionRepository(session)

    if repository.get_by_id(session_id) is None:
        raise InterviewSessionNotFoundError(
            "The requested interview session was not found."
        )

    questions = repository.list_questions_by_session_id(session_id)
    answers = repository.list_answers_by_session_id(session_id)

    evaluations: list[InterviewEvaluationResponse] = [
        evaluate_answer(
            session_id=session_id,
            answer_id=answer.id,
            session=session,
        )
        for answer in answers
    ]

    grouped: dict[
        InterviewQuestionCategory,
        list[InterviewEvaluationResponse],
    ] = {
        category: []
        for category in INTERVIEW_CATEGORIES
    }

    for answer, evaluation in zip(answers, evaluations):
        if answer.question_category in grouped:
            grouped[answer.question_category].append(evaluation)

    category_scores = {
        category: InterviewCategoryScore(
            average_overall_score=_average(
                evaluation.overall_score
                for evaluation in grouped[category]
            ),
            answer_count=len(grouped[category]),
        )
        for category in INTERVIEW_CATEGORIES
    }

    return InterviewSessionReport(
        session_id=session_id,
        total_questions=len(questions),
        answered_questions=len(answers),
        average_relevance_score=_average(
            evaluation.relevance_score
            for evaluation in evaluations
        ),
        average_completeness_score=_average(
            evaluation.completeness_score
            for evaluation in evaluations
        ),
        average_technical_score=_average(
            evaluation.technical_score
            for evaluation in evaluations
        ),
        overall_score=_average(
            evaluation.overall_score
            for evaluation in evaluations
        ),
        category_scores=category_scores,
        strengths=_unique_feedback(evaluations, "strengths"),
        improvements=_unique_feedback(evaluations, "improvements"),
    )