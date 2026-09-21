from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.skills import CategorizedSkillResult

if TYPE_CHECKING:
    from app.models.resume_analysis import ResumeAnalysis
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

    analysis: Mapped[ResumeAnalysis | None] = relationship(
        "ResumeAnalysis",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )


class ResumeUploadResponse(BaseModel):
    original_filename: str
    content_type: str
    stored_filename: str


class ResumeTextResponse(BaseModel):
    stored_filename: str
    text: str


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    original_filename: str
    stored_filename: str
    content_type: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Structured resume models
# ---------------------------------------------------------------------------

ResumeSectionType = Literal[
    "profile",
    "summary",
    "skills",
    "education",
    "experience",
    "projects",
    "certifications",
    "training",
    "achievements",
    "awards",
    "research",
    "publications",
    "volunteering",
    "leadership",
    "interests",
    "languages",
    "custom",
]


class ResumeEntry(BaseModel):
    """
    Generic fallback entry.

    Used when CareerLens knows that a piece of content belongs to a
    section but does not have enough evidence to map it to a specialized
    entity such as EducationEntry or ProjectEntry.
    """

    title: str | None = None
    content: list[str] = Field(default_factory=list)
    raw_text: str = ""


class EducationEntry(BaseModel):
    """Structured academic record."""

    institution: str | None = None
    location: str | None = None

    degree: str | None = None
    field_of_study: str | None = None

    start_date: str | None = None
    end_date: str | None = None
    expected_graduation: str | None = None

    gpa: str | None = None
    coursework: list[str] = Field(default_factory=list)

    raw_text: str = ""


class ExperienceEntry(BaseModel):
    """Structured professional or internship experience."""

    organization: str | None = None
    role: str | None = None
    location: str | None = None

    start_date: str | None = None
    end_date: str | None = None

    description: list[str] = Field(default_factory=list)

    raw_text: str = ""


class ProjectEntry(BaseModel):
    """Structured project record."""

    title: str | None = None
    technologies: list[str] = Field(default_factory=list)
    url: str | None = None

    description: list[str] = Field(default_factory=list)

    raw_text: str = ""


class CredentialEntry(BaseModel):
    """
    Structured certification / achievement / competition record.
    """

    title: str
    issuer: str | None = None

    credential_type: Literal[
        "certification",
        "achievement",
        "competition",
        "participation",
        "other",
    ] = "other"

    date: str | None = None
    url: str | None = None

    raw_text: str = ""


class ResumeSection(BaseModel):
    """
    General section representation.

    Important sections are additionally represented by typed fields
    in StructuredResume. This model allows CareerLens to preserve
    sections it does not yet understand.
    """

    title: str
    canonical_type: ResumeSectionType
    entries: list[ResumeEntry] = Field(default_factory=list)
    raw_content: list[str] = Field(default_factory=list)


class StructuredResume(BaseModel):
    """
    Canonical CareerLens representation of a resume.

    The typed fields are the source of truth for CareerLens intelligence.
    Legacy string fields are retained temporarily so existing services
    do not break while the rest of the application migrates.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    name: str | None = None
    email: str | None = None

    # ------------------------------------------------------------------
    # High-level profile
    # ------------------------------------------------------------------

    summary: str | None = None

    # ------------------------------------------------------------------
    # Legacy compatibility fields
    # ------------------------------------------------------------------

    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Canonical typed entities
    # ------------------------------------------------------------------

    education_entries: list[EducationEntry] = Field(default_factory=list)
    experience_entries: list[ExperienceEntry] = Field(default_factory=list)
    project_entries: list[ProjectEntry] = Field(default_factory=list)
    credential_entries: list[CredentialEntry] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Generalized sections
    # ------------------------------------------------------------------

    sections: list[ResumeSection] = Field(default_factory=list)


class ResumeAnalysisResponse(BaseModel):
    structured_resume: StructuredResume
    categorized_skills: CategorizedSkillResult