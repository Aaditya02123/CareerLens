from app.core.database import Base, engine
from app.models.application import Application  # noqa: F401
from app.models.interview_session import (  # noqa: F401
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
)
from app.models.interview_execution import (  # noqa: F401
    InterviewAdaptiveDecision,
    InterviewExecutionSession,
    InterviewSessionAnswer,
    InterviewSessionQuestion,
)
from app.models.interview_scorecard import (  # noqa: F401
    CriterionEvaluation,
    InterviewAnswerEvaluation,
    InterviewScorecard,
)
from app.models.interview_blueprint import (  # noqa: F401
    BlueprintCompetency,
    BlueprintQuestion,
    BlueprintRubricCriterion,
    InterviewBlueprint,
)
from app.models.learning_preferences import (  # noqa: F401
    UserLearningPreferences,
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
