from app.core.database import Base, engine
from app.models.resume import Resume  # noqa: F401
from app.models.user import User  # noqa: F401


def init_db() -> None:
    """Create database tables for all registered SQLAlchemy models."""
    Base.metadata.create_all(bind=engine)