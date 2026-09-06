from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.resume import Resume


class ResumeRepository:
    """Database operations for the Resume model."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        user_id: int,
        original_filename: str,
        stored_filename: str,
        content_type: str,
    ) -> Resume:
        """Create and persist a resume record."""
        resume = Resume(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=content_type,
        )

        self.session.add(resume)

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

        self.session.refresh(resume)
        return resume

    def get_by_id(self, resume_id: int) -> Resume | None:
        """Return a resume by ID, if one exists."""
        statement = select(Resume).where(Resume.id == resume_id)
        return self.session.scalar(statement)

    def get_by_user_id(self, user_id: int) -> list[Resume]:
        """Return all resumes belonging to a user."""
        statement = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.id)
        )

        return list(self.session.scalars(statement).all())