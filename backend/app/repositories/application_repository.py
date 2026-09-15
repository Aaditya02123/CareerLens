from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.application import Application


class ApplicationRepository:
    """Database operations for applications."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        user_id: int,
        job_id: int,
        status: str,
        notes: str | None,
    ) -> Application:
        """Create and persist an application."""
        application = Application(
            user_id=user_id,
            job_id=job_id,
            status=status,
            notes=notes,
        )

        self.session.add(application)

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(application)
        return application

    def get_by_id(
        self,
        application_id: int,
    ) -> Application | None:
        """Return an application by ID."""
        statement = select(Application).where(
            Application.id == application_id
        )
        return self.session.scalar(statement)

    def get_by_user_and_job(
        self,
        user_id: int,
        job_id: int,
    ) -> Application | None:
        """Return an application for a user and job."""
        statement = select(Application).where(
            Application.user_id == user_id,
            Application.job_id == job_id,
        )
        return self.session.scalar(statement)

    def list_by_user_id(
        self,
        user_id: int,
    ) -> list[Application]:
        """Return all applications belonging to a user."""
        statement = (
            select(Application)
            .where(Application.user_id == user_id)
            .order_by(
                Application.created_at.desc(),
                Application.id.desc(),
            )
        )

        return list(self.session.scalars(statement).all())

    def update_status(
        self,
        application: Application,
        status: str,
    ) -> Application:
        """Update and persist an application's status."""
        application.status = status

        try:
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        self.session.refresh(application)
        return application