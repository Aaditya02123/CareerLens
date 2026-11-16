from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.interview_blueprint import InterviewBlueprint
from app.models.interview_execution import (
    InterviewExecutionSession,
    InterviewExecutionSessionResponse,
    InterviewExecutionStatus,
    InterviewSessionAnswerCreate,
    InterviewSessionAnswerResponse,
    InterviewSessionQuestionResponse,
)
from app.repositories.interview_execution_repository import (
    DuplicateInterviewExecutionAnswerError,
    InterviewExecutionRepository,
)


class InterviewExecutionBlueprintNotFoundError(LookupError):
    """Raised when the source blueprint does not exist."""


class InterviewExecutionSessionNotFoundError(LookupError):
    """Raised when an executable interview session does not exist."""


class EmptyInterviewBlueprintError(ValueError):
    """Raised when a blueprint has no executable questions."""


class InvalidInterviewExecutionTransitionError(ValueError):
    """Raised when a session lifecycle transition is invalid."""


class InterviewExecutionAnswerError(ValueError):
    """Raised when an answer cannot be accepted."""


class InterviewExecutionService:
    def __init__(self, session: Session) -> None:
        self.repository = InterviewExecutionRepository(session)

    def _get_session(self, session_id: int) -> InterviewExecutionSession:
        record = self.repository.get_by_id(session_id)
        if record is None:
            raise InterviewExecutionSessionNotFoundError(
                "The requested interview session was not found."
            )
        return record

    @staticmethod
    def _response(
        record: InterviewExecutionSession,
        repository: InterviewExecutionRepository,
    ) -> InterviewExecutionSessionResponse:
        answered_ids = {answer.session_question_id for answer in record.answers}
        next_question = repository.get_next_unanswered_question(record)
        remaining = max(record.total_questions - record.answered_questions, 0)
        percentage = (
            0.0
            if record.total_questions == 0
            else min(record.answered_questions / record.total_questions * 100, 100.0)
        )

        # The next question is intentionally derived from persisted answers,
        # not from a client-supplied position.
        current_position = (
            next_question.question_order if next_question is not None else None
        )
        return InterviewExecutionSessionResponse(
            id=record.id,
            blueprint_id=record.blueprint_id,
            status=record.status,
            created_at=record.created_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            total_questions=record.total_questions,
            answered_questions=len(answered_ids),
            remaining_questions=remaining,
            completion_percentage=percentage,
            current_question_position=current_position,
            next_question=(
                InterviewSessionQuestionResponse.model_validate(next_question)
                if next_question is not None
                else None
            ),
            answers=[
                InterviewSessionAnswerResponse.model_validate(answer)
                for answer in sorted(
                    record.answers,
                    key=lambda item: item.question_order,
                )
            ],
        )

    def create_session(
        self,
        blueprint_id: int,
    ) -> InterviewExecutionSessionResponse:
        blueprint = self.repository.get_blueprint(blueprint_id)
        if blueprint is None:
            raise InterviewExecutionBlueprintNotFoundError(
                "The requested interview blueprint was not found."
            )
        if not blueprint.questions:
            raise EmptyInterviewBlueprintError(
                "The interview blueprint contains no questions."
            )

        record = self.repository.create_from_blueprint(blueprint)
        return self._response(record, self.repository)

    def get_session(
        self,
        session_id: int,
    ) -> InterviewExecutionSessionResponse:
        record = self._get_session(session_id)
        return self._response(record, self.repository)

    def start_session(
        self,
        session_id: int,
    ) -> InterviewExecutionSessionResponse:
        record = self._get_session(session_id)
        if record.status != InterviewExecutionStatus.CREATED:
            raise InvalidInterviewExecutionTransitionError(
                "Only a created interview session can be started."
            )
        updated = self.repository.start(record)
        return self._response(updated, self.repository)

    def submit_answer(
        self,
        session_id: int,
        answer_data: InterviewSessionAnswerCreate,
    ) -> InterviewExecutionSessionResponse:
        record = self._get_session(session_id)
        if record.status != InterviewExecutionStatus.IN_PROGRESS:
            raise InvalidInterviewExecutionTransitionError(
                "Answers can only be submitted to an in-progress session."
            )
        if not answer_data.answer.strip():
            raise InterviewExecutionAnswerError("Answer cannot be empty.")

        question = self.repository.get_next_unanswered_question(record)
        if question is None:
            raise InterviewExecutionAnswerError(
                "No unanswered interview question remains."
            )

        try:
            self.repository.create_answer_and_advance(
                session_record=record,
                question=question,
                answer_text=answer_data.answer,
            )
        except DuplicateInterviewExecutionAnswerError:
            raise

        refreshed = self._get_session(session_id)
        return self._response(refreshed, self.repository)
