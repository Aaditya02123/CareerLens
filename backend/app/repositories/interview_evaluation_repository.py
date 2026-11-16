from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload
from psycopg.errors import UniqueViolation

from app.models.interview_scorecard import (
    CriterionEvaluation,
    InterviewAnswerEvaluation,
    InterviewScorecard,
)


class InterviewEvaluationRepository:
    """Persistence operations for answer evaluations and scorecards."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_answer_id(
        self,
        session_id: int,
        answer_id: int,
    ) -> InterviewAnswerEvaluation | None:
        statement = (
            select(InterviewAnswerEvaluation)
            .options(selectinload(InterviewAnswerEvaluation.criteria))
            .where(
                InterviewAnswerEvaluation.session_id == session_id,
                InterviewAnswerEvaluation.answer_id == answer_id,
            )
        )
        return self.session.scalar(statement)

    def list_by_session_id(
        self,
        session_id: int,
    ) -> list[InterviewAnswerEvaluation]:
        statement = (
            select(InterviewAnswerEvaluation)
            .options(selectinload(InterviewAnswerEvaluation.criteria))
            .where(InterviewAnswerEvaluation.session_id == session_id)
            .order_by(InterviewAnswerEvaluation.answer_id.asc())
        )
        return list(self.session.scalars(statement).all())

    def get_scorecard(self, session_id: int) -> InterviewScorecard | None:
        statement = select(InterviewScorecard).where(
            InterviewScorecard.session_id == session_id
        )
        return self.session.scalar(statement)

    def persist_evaluation(
        self,
        *,
        session_id: int,
        answer_id: int,
        question_id: int,
        competency_reference: str,
        weighted_score: float,
        strengths: list[str],
        improvement_areas: list[str],
        actionable_feedback: list[str],
        provider_name: str,
        criterion_rows: list[dict],
        scorecard: dict,
    ) -> InterviewAnswerEvaluation:
        evaluation = InterviewAnswerEvaluation(
            session_id=session_id,
            answer_id=answer_id,
            question_id=question_id,
            competency_reference=competency_reference,
            weighted_score=weighted_score,
            strengths=strengths,
            improvement_areas=improvement_areas,
            actionable_feedback=actionable_feedback,
            evaluation_status="complete",
            provider_name=provider_name,
        )
        self.session.add(evaluation)

        try:
            self.session.flush()
            for row in criterion_rows:
                self.session.add(
                    CriterionEvaluation(
                        evaluation_id=evaluation.id,
                        **row,
                    )
                )

            scorecard_record = self.get_scorecard(session_id)
            if scorecard_record is None:
                scorecard_record = InterviewScorecard(
                    session_id=session_id,
                    **scorecard,
                )
                self.session.add(scorecard_record)
            else:
                for key, value in scorecard.items():
                    setattr(scorecard_record, key, value)

            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            original = error.orig
            diagnostic = getattr(original, "diag", None)
            constraint_name = getattr(diagnostic, "constraint_name", None)
            if isinstance(original, UniqueViolation) and constraint_name in {
                "uq_interview_answer_evaluation_answer",
                "uq_interview_scorecard_session",
            }:
                existing = self.get_by_answer_id(session_id, answer_id)
                if existing is not None:
                    return existing
            raise
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(evaluation)
        return self.get_by_answer_id(session_id, answer_id) or evaluation
