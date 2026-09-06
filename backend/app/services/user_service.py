from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    """Business logic for users."""

    def __init__(self, session: Session) -> None:
        self.repository = UserRepository(session)

    def create_user(self, email: str, name: str) -> User:
        """Create a user through the repository."""
        return self.repository.create(email=email, name=name)