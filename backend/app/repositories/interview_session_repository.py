from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.interview_session import (
    InterviewAnswer,
    InterviewSession,
    InterviewSessionStatus,
)


class InterviewSessionRepository:
    """Database operations for interview sessions and answers."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_session(
        self,
        user_id: int,
        resume_id: int,
        job_id: int,
        status: InterviewSessionStatus,
    ) -> InterviewSession:
        """Create and persist an interview session."""
        interview_session = InterviewSession(
            user_id=user_id,
            resume_id=resume_id,
            job_id=job_id,
            status=status,
        )

        self.session.add(interview_session)

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(interview_session)
        return interview_session

    def get_by_id(
        self,
        session_id: int,
    ) -> InterviewSession | None:
        """Return an interview session by ID."""
        statement = select(InterviewSession).where(
            InterviewSession.id == session_id
        )
        return self.session.scalar(statement)

    def list_by_user_id(
        self,
        user_id: int,
    ) -> list[InterviewSession]:
        """Return all interview sessions for a user."""
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
        """Update and persist a session status."""
        interview_session.status = status

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(interview_session)
        return interview_session

    def create_answer(
        self,
        session_id: int,
        question: str,
        answer: str,
        question_category: str,
    ) -> InterviewAnswer:
        """Create and persist an answer."""
        interview_answer = InterviewAnswer(
            session_id=session_id,
            question=question,
            answer=answer,
            question_category=question_category,
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
        """Return answers for an interview session."""
        statement = (
            select(InterviewAnswer)
            .where(InterviewAnswer.session_id == session_id)
            .order_by(
                InterviewAnswer.created_at.asc(),
                InterviewAnswer.id.asc(),
            )
        )

        return list(self.session.scalars(statement).all())