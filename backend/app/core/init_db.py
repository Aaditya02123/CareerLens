from app.core.database import Base, engine
from app.models.application import Application  # noqa: F401
from app.models.interview_session import (  # noqa: F401
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
)
from app.models.jobs import Job  # noqa: F401
from app.models.learning_roadmap_db import (  # noqa: F401
    LearningRoadmap,
    LearningRoadmapItem,
)
from app.models.resume import Resume  # noqa: F401
from app.models.resume_analysis import ResumeAnalysis  # noqa: F401
from app.models.user import User  # noqa: F401


def init_db() -> None:
    """Create database tables for all registered SQLAlchemy models."""
    Base.metadata.create_all(bind=engine)