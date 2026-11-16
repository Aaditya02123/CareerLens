from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload
from psycopg.errors import UniqueViolation

from app.models.interview_blueprint import InterviewBlueprint
from app.models.interview_execution import (
    InterviewExecutionSession,
    InterviewExecutionStatus,
    InterviewSessionAnswer,
    InterviewSessionQuestion,
)


class DuplicateInterviewExecutionAnswerError(ValueError):
    """Raised when an execution question already has an answer."""


DUPLICATE_EXECUTION_ANSWER_CONSTRAINT = (
    "uq_execution_answer_session_question"
)


def _is_duplicate_answer_violation(error: IntegrityError) -> bool:
    original = error.orig
    if not isinstance(original, UniqueViolation):
        return False
    diagnostic = getattr(original, "diag", None)
    return getattr(
        diagnostic,
        "constraint_name",
        None,
    ) == DUPLICATE_EXECUTION_ANSWER_CONSTRAINT


class InterviewExecutionRepository:
    """Persistence operations for executable blueprint sessions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_blueprint(self, blueprint_id: int) -> InterviewBlueprint | None:
        statement = (
            select(InterviewBlueprint)
            .options(selectinload(InterviewBlueprint.questions))
            .where(InterviewBlueprint.id == blueprint_id)
        )
        return self.session.scalar(statement)

    def create_from_blueprint(
        self,
        blueprint: InterviewBlueprint,
    ) -> InterviewExecutionSession:
        session_record = InterviewExecutionSession(
            blueprint_id=blueprint.id,
            status=InterviewExecutionStatus.CREATED,
            total_questions=len(blueprint.questions),
            answered_questions=0,
        )
        self.session.add(session_record)

        try:
            self.session.flush()
            for order, question in enumerate(
                sorted(blueprint.questions, key=lambda item: item.question_order),
                start=1,
            ):
                self.session.add(
                    InterviewSessionQuestion(
                        session_id=session_record.id,
                        blueprint_question_id=question.id,
                        question_order=order,
                        question=question.question,
                        question_category=question.category,
                        difficulty=question.difficulty,
                        target_competency=question.target_competency,
                        assessment_objective=question.assessment_objective,
                        relevance_reason=question.relevance_reason,
                    )
                )
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        return self.get_by_id(session_record.id) or session_record

    def get_by_id(
        self,
        session_id: int,
    ) -> InterviewExecutionSession | None:
        statement = (
            select(InterviewExecutionSession)
            .options(
                selectinload(InterviewExecutionSession.questions),
                selectinload(InterviewExecutionSession.answers),
            )
            .where(InterviewExecutionSession.id == session_id)
        )
        return self.session.scalar(statement)

    def get_next_unanswered_question(
        self,
        session_record: InterviewExecutionSession,
    ) -> InterviewSessionQuestion | None:
        answered_ids = {
            answer.session_question_id
            for answer in session_record.answers
        }
        for question in sorted(
            session_record.questions,
            key=lambda item: item.question_order,
        ):
            if question.id not in answered_ids:
                return question
        return None

    def get_answer_by_question(
        self,
        session_id: int,
        question_id: int,
    ) -> InterviewSessionAnswer | None:
        statement = select(InterviewSessionAnswer).where(
            InterviewSessionAnswer.session_id == session_id,
            InterviewSessionAnswer.session_question_id == question_id,
        )
        return self.session.scalar(statement)

    def start(
        self,
        session_record: InterviewExecutionSession,
    ) -> InterviewExecutionSession:
        session_record.status = InterviewExecutionStatus.IN_PROGRESS
        session_record.started_at = datetime.now(timezone.utc)
        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise
        self.session.refresh(session_record)
        return session_record

    def create_answer_and_advance(
        self,
        session_record: InterviewExecutionSession,
        question: InterviewSessionQuestion,
        answer_text: str,
    ) -> InterviewSessionAnswer:
        answer = InterviewSessionAnswer(
            session_id=session_record.id,
            session_question_id=question.id,
            question_order=question.question_order,
            answer=answer_text,
        )
        self.session.add(answer)
        session_record.answered_questions += 1

        if session_record.answered_questions >= session_record.total_questions:
            session_record.status = InterviewExecutionStatus.COMPLETED
            session_record.completed_at = datetime.now(timezone.utc)

        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            if _is_duplicate_answer_violation(error):
                raise DuplicateInterviewExecutionAnswerError(
                    "This interview question already has an answer."
                ) from error
            raise
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(answer)
        return answer
