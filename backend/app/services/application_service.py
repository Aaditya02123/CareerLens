from sqlalchemy.orm import Session

from app.models.application import (
    Application,
    ApplicationCreate,
    ApplicationStatus,
)
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.repositories.user_repository import UserRepository


class ApplicationNotFoundError(LookupError):
    """Raised when an application does not exist."""


class UserNotFoundError(LookupError):
    """Raised when a referenced user does not exist."""


class JobNotFoundError(LookupError):
    """Raised when a referenced job does not exist."""


class DuplicateApplicationError(RuntimeError):
    """Raised when a user already tracks a job."""


ALLOWED_STATUS_TRANSITIONS = {
    ApplicationStatus.SAVED: {
        ApplicationStatus.SAVED,
        ApplicationStatus.APPLIED,
        ApplicationStatus.REJECTED,
    },
    ApplicationStatus.APPLIED: {
        ApplicationStatus.APPLIED,
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.REJECTED,
    },
    ApplicationStatus.INTERVIEW: {
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
    },
    ApplicationStatus.OFFER: {
        ApplicationStatus.OFFER,
    },
    ApplicationStatus.REJECTED: {
        ApplicationStatus.REJECTED,
    },
}


class ApplicationService:
    """Business logic for application tracking."""

    def __init__(self, session: Session) -> None:
        self.application_repository = ApplicationRepository(session)
        self.user_repository = UserRepository(session)
        self.job_repository = JobRepository(session)

    @staticmethod
    def _parse_status(status: str) -> ApplicationStatus:
        try:
            return ApplicationStatus(status.strip().lower())
        except ValueError as error:
            raise ValueError(
                "Invalid application status."
            ) from error

    def create_application(
        self,
        application_data: ApplicationCreate,
    ) -> Application:
        """Create an application after validating its references."""
        if self.user_repository.get_by_id(
            application_data.user_id
        ) is None:
            raise UserNotFoundError("The specified user was not found.")

        if self.job_repository.get_by_id(
            application_data.job_id
        ) is None:
            raise JobNotFoundError("The specified job was not found.")

        if self.application_repository.get_by_user_and_job(
            application_data.user_id,
            application_data.job_id,
        ) is not None:
            raise DuplicateApplicationError(
                "This user already has an application for the job."
            )

        status = self._parse_status(application_data.status)

        return self.application_repository.create(
            user_id=application_data.user_id,
            job_id=application_data.job_id,
            status=status.value,
            notes=application_data.notes,
        )

    def get_application(
        self,
        application_id: int,
    ) -> Application:
        """Return an application by ID."""
        application = self.application_repository.get_by_id(
            application_id
        )

        if application is None:
            raise ApplicationNotFoundError(
                "The requested application was not found."
            )

        return application

    def list_applications_for_user(
        self,
        user_id: int,
    ) -> list[Application]:
        """Return all applications for a user."""
        if self.user_repository.get_by_id(user_id) is None:
            raise UserNotFoundError("The specified user was not found.")

        return self.application_repository.list_by_user_id(user_id)

    def update_application_status(
        self,
        application_id: int,
        new_status: str,
    ) -> Application:
        """Update an application status when the transition is valid."""
        application = self.get_application(application_id)
        parsed_status = self._parse_status(new_status)

        current_status = self._parse_status(application.status)
        allowed_statuses = ALLOWED_STATUS_TRANSITIONS[current_status]

        if parsed_status not in allowed_statuses:
            raise ValueError(
                f"Cannot change application status from "
                f"{current_status.value} to {parsed_status.value}."
            )

        if parsed_status == current_status:
            return application

        return self.application_repository.update_status(
            application=application,
            status=parsed_status.value,
        )