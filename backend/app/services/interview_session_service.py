from sqlalchemy.orm import Session

from app.models.interview_session import (
    InterviewAnswer,
    InterviewAnswerCreate,
    InterviewSession,
    InterviewSessionCreate,
    InterviewSessionStatus,
)
from app.repositories.interview_session_repository import (
    InterviewSessionRepository,
)
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository


class UserNotFoundError(LookupError):
    """Raised when a referenced user does not exist."""


class ResumeNotFoundError(LookupError):
    """Raised when a referenced resume does not exist."""


class JobNotFoundError(LookupError):
    """Raised when a referenced job does not exist."""


class ResumeOwnershipError(ValueError):
    """Raised when a resume belongs to a different user."""


class InterviewSessionNotFoundError(LookupError):
    """Raised when an interview session does not exist."""


class InactiveInterviewSessionError(ValueError):
    """Raised when an inactive session is used for a new answer."""


ALLOWED_SESSION_TRANSITIONS = {
    InterviewSessionStatus.ACTIVE: {
        InterviewSessionStatus.ACTIVE,
        InterviewSessionStatus.COMPLETED,
        InterviewSessionStatus.ABANDONED,
    },
    InterviewSessionStatus.COMPLETED: {
        InterviewSessionStatus.COMPLETED,
    },
    InterviewSessionStatus.ABANDONED: {
        InterviewSessionStatus.ABANDONED,
    },
}


class InterviewSessionService:
    """Business logic for mock interview sessions."""

    def __init__(self, session: Session) -> None:
        self.repository = InterviewSessionRepository(session)
        self.user_repository = UserRepository(session)
        self.resume_repository = ResumeRepository(session)
        self.job_repository = JobRepository(session)

    @staticmethod
    def _parse_status(
        status: str | InterviewSessionStatus,
    ) -> InterviewSessionStatus:
        if isinstance(status, InterviewSessionStatus):
            return status

        try:
            return InterviewSessionStatus(status.strip().lower())
        except ValueError as error:
            raise ValueError(
                "Invalid interview session status."
            ) from error

    def create_session(
        self,
        session_data: InterviewSessionCreate,
    ) -> InterviewSession:
        """Create an active interview session after ownership checks."""
        if self.user_repository.get_by_id(session_data.user_id) is None:
            raise UserNotFoundError("The specified user was not found.")

        resume = self.resume_repository.get_by_id(
            session_data.resume_id
        )

        if resume is None:
            raise ResumeNotFoundError(
                "The specified resume was not found."
            )

        if resume.user_id != session_data.user_id:
            raise ResumeOwnershipError(
                "The resume does not belong to the specified user."
            )

        if self.job_repository.get_by_id(session_data.job_id) is None:
            raise JobNotFoundError("The specified job was not found.")

        return self.repository.create_session(
            user_id=session_data.user_id,
            resume_id=session_data.resume_id,
            job_id=session_data.job_id,
            status=InterviewSessionStatus.ACTIVE,
        )

    def get_session(
        self,
        session_id: int,
    ) -> InterviewSession:
        """Return an interview session by ID."""
        interview_session = self.repository.get_by_id(session_id)

        if interview_session is None:
            raise InterviewSessionNotFoundError(
                "The requested interview session was not found."
            )

        return interview_session

    def list_sessions_for_user(
        self,
        user_id: int,
    ) -> list[InterviewSession]:
        """Return all interview sessions for a user."""
        if self.user_repository.get_by_id(user_id) is None:
            raise UserNotFoundError("The specified user was not found.")

        return self.repository.list_by_user_id(user_id)

    def update_session_status(
        self,
        session_id: int,
        new_status: str,
    ) -> InterviewSession:
        """Update a session status when the transition is valid."""
        interview_session = self.get_session(session_id)
        parsed_status = self._parse_status(new_status)
        current_status = self._parse_status(interview_session.status)

        if parsed_status not in ALLOWED_SESSION_TRANSITIONS[
            current_status
        ]:
            raise ValueError(
                f"Cannot change interview session status from "
                f"{current_status.value} to {parsed_status.value}."
            )

        if parsed_status == current_status:
            return interview_session

        return self.repository.update_status(
            interview_session=interview_session,
            status=parsed_status,
        )

    def submit_answer(
        self,
        session_id: int,
        answer_data: InterviewAnswerCreate,
    ) -> InterviewAnswer:
        """Store an answer only for an active interview session."""
        interview_session = self.get_session(session_id)
        current_status = self._parse_status(interview_session.status)

        if current_status != InterviewSessionStatus.ACTIVE:
            raise InactiveInterviewSessionError(
                "Answers can only be submitted to an active session."
            )

        if not answer_data.question.strip():
            raise ValueError("Question cannot be empty.")

        if not answer_data.answer.strip():
            raise ValueError("Answer cannot be empty.")

        if not answer_data.question_category.strip():
            raise ValueError(
                "Question category cannot be empty."
            )

        return self.repository.create_answer(
            session_id=session_id,
            question=answer_data.question,
            answer=answer_data.answer,
            question_category=answer_data.question_category,
        )

    def list_answers(
        self,
        session_id: int,
    ) -> list[InterviewAnswer]:
        """Return answers for an existing session."""
        self.get_session(session_id)
        return self.repository.list_answers_by_session_id(session_id)