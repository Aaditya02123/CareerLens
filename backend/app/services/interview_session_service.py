from sqlalchemy.orm import Session

from app.models.interview_session import (
    InterviewAnswer,
    InterviewAnswerCreate,
    InterviewQuestionResponse,
    InterviewSession,
    InterviewSessionCreate,
    InterviewSessionProgressResponse,
    InterviewSessionStatus,
)
from app.repositories.interview_session_repository import (
    DuplicateInterviewAnswerError,
    InterviewSessionRepository,
)
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.services.interview_preparation_service import (
    build_interview_preparation,
)


class UserNotFoundError(LookupError):
    pass


class ResumeNotFoundError(LookupError):
    pass


class JobNotFoundError(LookupError):
    pass


class ResumeOwnershipError(ValueError):
    pass


class InterviewSessionNotFoundError(LookupError):
    pass


class InterviewQuestionNotFoundError(LookupError):
    pass


class NoUnansweredInterviewQuestionError(LookupError):
    pass


class InterviewQuestionOwnershipError(ValueError):
    pass


class InactiveInterviewSessionError(ValueError):
    pass


class InvalidInterviewSessionStatusTransitionError(ValueError):
    pass


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
    def __init__(self, session: Session) -> None:
        self.session = session
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

    @staticmethod
    def _build_transition_error_message(
        current_status: InterviewSessionStatus,
        requested_status: InterviewSessionStatus,
    ) -> str:
        return (
            f"Interview session is already {current_status.value} "
            f"and cannot transition to {requested_status.value}."
        )

    def create_session(
        self,
        session_data: InterviewSessionCreate,
    ) -> InterviewSession:
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

        preparation = build_interview_preparation(
            resume_id=session_data.resume_id,
            job_id=session_data.job_id,
            session=self.session,
        )

        return self.repository.create_session_with_questions(
            user_id=session_data.user_id,
            resume_id=session_data.resume_id,
            job_id=session_data.job_id,
            status=InterviewSessionStatus.ACTIVE,
            questions=preparation.questions,
        )

    def get_session(self, session_id: int) -> InterviewSession:
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
        if self.user_repository.get_by_id(user_id) is None:
            raise UserNotFoundError("The specified user was not found.")

        return self.repository.list_by_user_id(user_id)

    def list_questions(
        self,
        session_id: int,
    ) -> list[InterviewQuestionResponse]:
        self.get_session(session_id)

        questions = self.repository.list_questions_by_session_id(
            session_id
        )
        answered_question_ids = (
            self.repository.list_answered_question_ids_by_session_id(
                session_id
            )
        )

        return [
            InterviewQuestionResponse.model_validate(question).model_copy(
                update={
                    "answered": question.id in answered_question_ids
                }
            )
            for question in questions
        ]

    def get_next_question(
        self,
        session_id: int,
    ) -> InterviewQuestionResponse:
        self.get_session(session_id)

        question = self.repository.get_next_unanswered_question(
            session_id
        )

        if question is None:
            raise NoUnansweredInterviewQuestionError(
                "No unanswered interview questions remain."
            )

        return InterviewQuestionResponse.model_validate(
            question
        ).model_copy(update={"answered": False})

    def get_session_progress(
        self,
        session_id: int,
    ) -> InterviewSessionProgressResponse:
        interview_session = self.get_session(session_id)
        total_questions = self.repository.count_questions_by_session_id(
            session_id
        )
        answered_questions = self.repository.count_answers_by_session_id(
            session_id
        )

        remaining_questions = max(
            total_questions - answered_questions,
            0,
        )

        if total_questions == 0:
            progress_percentage = 0.0
        else:
            progress_percentage = min(
                (answered_questions / total_questions) * 100,
                100.0,
            )

        return InterviewSessionProgressResponse(
            session_id=session_id,
            status=self._parse_status(interview_session.status),
            total_questions=total_questions,
            answered_questions=answered_questions,
            remaining_questions=remaining_questions,
            progress_percentage=progress_percentage,
        )

    def update_session_status(
        self,
        session_id: int,
        new_status: str | InterviewSessionStatus,
    ) -> InterviewSession:
        interview_session = self.get_session(session_id)
        parsed_status = self._parse_status(new_status)
        current_status = self._parse_status(interview_session.status)

        if parsed_status == current_status:
            return interview_session

        if parsed_status not in ALLOWED_SESSION_TRANSITIONS[
            current_status
        ]:
            raise InvalidInterviewSessionStatusTransitionError(
                self._build_transition_error_message(
                    current_status=current_status,
                    requested_status=parsed_status,
                )
            )

        return self.repository.update_status(
            interview_session=interview_session,
            status=parsed_status,
        )

    def submit_answer(
        self,
        session_id: int,
        answer_data: InterviewAnswerCreate,
    ) -> InterviewAnswer:
        interview_session = self.get_session(session_id)

        if self._parse_status(interview_session.status) != (
            InterviewSessionStatus.ACTIVE
        ):
            raise InactiveInterviewSessionError(
                "Answers can only be submitted to an active session."
            )

        if not answer_data.answer.strip():
            raise ValueError("Answer cannot be empty.")

        question = self.repository.get_question_by_id(
            answer_data.question_id
        )

        if question is None:
            raise InterviewQuestionNotFoundError(
                "The specified interview question was not found."
            )

        if question.session_id != session_id:
            raise InterviewQuestionOwnershipError(
                "The question does not belong to the specified session."
            )

        if self.repository.answer_exists_for_question(
            session_id=session_id,
            question_id=question.id,
        ):
            raise DuplicateInterviewAnswerError(
                "This interview question already has an answer."
            )

        return self.repository.create_answer(
            session_id=session_id,
            question=question,
            answer=answer_data.answer,
        )