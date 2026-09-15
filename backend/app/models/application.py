from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ApplicationStatus(str, Enum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


class Application(Base):
    """Database model representing a user's job application."""

    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_id",
            name="uq_applications_user_job",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ApplicationCreate(BaseModel):
    """Request schema for creating an application."""

    user_id: int
    job_id: int
    status: str
    notes: str | None = None


class ApplicationStatusUpdate(BaseModel):
    """Request schema for changing application status."""

    status: str


class ApplicationResponse(BaseModel):
    """Response schema for an application."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    job_id: int
    status: ApplicationStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime