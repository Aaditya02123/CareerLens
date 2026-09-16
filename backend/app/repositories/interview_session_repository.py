from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.interview_preparation import (
    InterviewQuestion as GeneratedQuestion,
)
from app.models.interview_session import (
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
    InterviewSessionStatus,
)


class InterviewSessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_session_with_questions(
        self,
        user_id: int,
        resume_id: int,
        job_id: int,
        status: InterviewSessionStatus,
        questions: list[GeneratedQuestion],
    ) -> InterviewSession:
        interview_session = InterviewSession(
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
            status=status,
        )
        self.session.add(interview_session)

        try:
            self.session.flush()

            for order, generated in enumerate(questions, start=1):
                self.session.add(
                    InterviewQuestion(
                        session_id=interview_session.id,
                        question=generated.question,
                        question_category=generated.category,
                        difficulty=generated.difficulty,
                        priority=generated.priority,
                        reason=generated.reason,
                        question_order=order,
                    )
                )

            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(interview_session)
        return interview_session

    def get_by_id(self, session_id: int) -> InterviewSession | None:
        return self.session.scalar(
            select(InterviewSession).where(
                InterviewSession.id == session_id
            )
        )

    def list_by_user_id(self, user_id: int) -> list[InterviewSession]:
        statement = (
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(
                InterviewSession.created_at.desc(),
                InterviewSession.id.desc(),
            )
        )
        return list(self.session.scalars(statement).all())

    def update_status(
        self,
        interview_session: InterviewSession,
        status: InterviewSessionStatus,
    ) -> InterviewSession:
        interview_session.status = status

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(interview_session)
        return interview_session

    def get_question_by_id(
        self,
        question_id: int,
    ) -> InterviewQuestion | None:
        return self.session.scalar(
            select(InterviewQuestion).where(
                InterviewQuestion.id == question_id
            )
        )

    def list_questions_by_session_id(
        self,
        session_id: int,
    ) -> list[InterviewQuestion]:
        statement = (
            select(InterviewQuestion)
            .where(InterviewQuestion.session_id == session_id)
            .order_by(
                InterviewQuestion.question_order.asc(),
                InterviewQuestion.id.asc(),
            )
        )
        return list(self.session.scalars(statement).all())

    def create_answer(
        self,
        session_id: int,
        question: InterviewQuestion,
        answer: str,
    ) -> InterviewAnswer:
        interview_answer = InterviewAnswer(
            session_id=session_id,
            question_id=question.id,
            question=question.question,
            answer=answer,
            question_category=question.question_category,
        )
        self.session.add(interview_answer)

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(interview_answer)
        return interview_answer

    def list_answers_by_session_id(
        self,
        session_id: int,
    ) -> list[InterviewAnswer]:
        statement = (
            select(InterviewAnswer)
            .where(InterviewAnswer.session_id == session_id)
            .order_by(
                InterviewAnswer.created_at.asc(),
                InterviewAnswer.id.asc(),
            )
        )
        return list(self.session.scalars(statement).all())