from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.resume import StructuredResume
from app.models.skills import CategorizedSkillResult

if TYPE_CHECKING:
    from app.models.resume import Resume


class ResumeAnalysis(Base):
    """Database model storing the latest analysis for a resume."""

    __tablename__ = "resume_analysis"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    structured_resume: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    categorized_skills: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    resume: Mapped[Resume] = relationship(
        "Resume",
        back_populates="analysis",
    )


class ResumeAnalysisRecordResponse(BaseModel):
    """API-compatible schema for a persisted resume analysis record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    structured_resume: StructuredResume
    categorized_skills: CategorizedSkillResult
    created_at: datetime