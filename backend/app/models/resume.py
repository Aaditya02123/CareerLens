from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.skills import CategorizedSkillResult

if TYPE_CHECKING:
    from app.models.user import User


class Resume(Base):
    """Database model representing a stored resume."""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="resumes",
    )


class ResumeUploadResponse(BaseModel):
    original_filename: str
    content_type: str
    stored_filename: str


class ResumeTextResponse(BaseModel):
    stored_filename: str
    text: str


class StructuredResume(BaseModel):
    name: str | None = None
    email: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)

class ResumeAnalysisResponse(BaseModel):
    structured_resume: StructuredResume
    categorized_skills: CategorizedSkillResult