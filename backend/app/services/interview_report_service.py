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


def _empty_category_scores() -> dict[
    InterviewQuestionCategory,
    InterviewCategoryScore,
]:
    """Return all known categories with zero scores."""
    return {
        category: InterviewCategoryScore()
        for category in INTERVIEW_CATEGORIES
    }


def _average(values: Iterable[float]) -> float:
    """Return an arithmetic mean or zero for an empty collection."""
    values_list = list(values)

    if not values_list:
        return 0.0

    return sum(values_list) / len(values_list)


def _unique_feedback(evaluations, field_name: str) -> list[str]:
    """Deduplicate feedback case-insensitively while preserving order."""
    feedback: list[str] = []
    seen: set[str] = set()

    for evaluation in evaluations:
        for item in getattr(evaluation, field_name):
            normalized_item = item.casefold()

            if normalized_item in seen:
                continue

            seen.add(normalized_item)
            feedback.append(item)

    return feedback


def generate_interview_session_report(
    session_id: int,
    session: Session,
) -> InterviewSessionReport:
    """Generate a report from the session's submitted answers.

    The current database model stores submitted answers but does not persist
    the full preparation question set. Therefore total_questions is based on
    the number of submitted answers available for this session.
    """
    repository = InterviewSessionRepository(session)
    interview_session = repository.get_by_id(session_id)

    if interview_session is None:
        raise InterviewSessionNotFoundError(
            "The requested interview session was not found."
        )

    answers = repository.list_answers_by_session_id(session_id)

    evaluations: list[InterviewEvaluationResponse] = [
        evaluate_answer(
            session_id=session_id,
            answer_id=answer.id,
            session=session,
        )
        for answer in answers
    ]

    answered_questions = len(evaluations)
    category_scores = _empty_category_scores()

    grouped_evaluations: dict[
        InterviewQuestionCategory,
        list[InterviewEvaluationResponse],
    ] = {
        category: []
        for category in INTERVIEW_CATEGORIES
    }

    for answer, evaluation in zip(answers, evaluations):
        category = answer.question_category

        if category in grouped_evaluations:
            grouped_evaluations[category].append(evaluation)

    for category, category_evaluations in grouped_evaluations.items():
        category_scores[category] = InterviewCategoryScore(
            average_overall_score=_average(
                evaluation.overall_score
                for evaluation in category_evaluations
            ),
            answer_count=len(category_evaluations),
        )

    return InterviewSessionReport(
        session_id=session_id,
        total_questions=answered_questions,
        answered_questions=answered_questions,
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
        strengths=_unique_feedback(
            evaluations,
            "strengths",
        ),
        improvements=_unique_feedback(
            evaluations,
            "improvements",
        ),
    )