from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Database operations for the User model."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, email: str, name: str) -> User:
        """Create and persist a new user."""
        user = User(
            email=email,
            name=name,
        )

        self.session.add(user)

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

        self.session.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> User | None:
        """Return a user by ID, if one exists."""
        statement = select(User).where(User.id == user_id)
        return self.session.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        """Return a user by email, if one exists."""
        statement = select(User).where(User.email == email)
        return self.session.scalar(statement)