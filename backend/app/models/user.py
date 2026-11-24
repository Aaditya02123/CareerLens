from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.learning_preferences import UserLearningPreferences
    from app.models.resume import Resume


class User(Base):
    """Database model representing a CareerLens user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    resumes: Mapped[list[Resume]] = relationship(
        "Resume",
        back_populates="user",
    )

    learning_preferences: Mapped[UserLearningPreferences | None] = relationship(
        "UserLearningPreferences",
        back_populates="user",
        uselist=False,
    )


class UserCreate(BaseModel):
    """Request schema for creating a user."""

    email: str
    name: str
    password: str


class UserResponse(BaseModel):
    """Response schema for a user."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    created_at: datetime
