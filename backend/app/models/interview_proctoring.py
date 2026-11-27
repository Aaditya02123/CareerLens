from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProctoringEventType(str, Enum):
    TAB_SWITCH = "tab_switch"
    WINDOW_BLUR = "window_blur"
    PASTE_DETECTED = "paste_detected"
    NO_FACE = "no_face"
    MULTIPLE_FACES = "multiple_faces"
    AUDIO_ANOMALY = "audio_anomaly"


class ProctoringSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProctoringEvent(Base):
    """Integrity and telemetry event captured during an interview session."""

    __tablename__ = "interview_proctoring_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_execution_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[ProctoringEventType] = mapped_column(
        SQLAlchemyEnum(ProctoringEventType, name="proctoring_event_type"),
        nullable=False,
    )
    severity: Mapped[ProctoringSeverity] = mapped_column(
        SQLAlchemyEnum(ProctoringSeverity, name="proctoring_severity"),
        nullable=False,
        default=ProctoringSeverity.MEDIUM,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )


class ProctoringEventCreate(BaseModel):
    event_type: ProctoringEventType
    severity: ProctoringSeverity = ProctoringSeverity.MEDIUM
    details: dict[str, Any] = Field(default_factory=dict)


class ProctoringEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    event_type: ProctoringEventType
    severity: ProctoringSeverity
    timestamp: datetime
    details: dict[str, Any] = Field(default_factory=dict)


class ProctoringTimelineItem(BaseModel):
    id: int
    event_type: str
    severity: str
    timestamp: datetime
    label: str
    details: dict[str, Any] = Field(default_factory=dict)


class ProctoringSummaryResponse(BaseModel):
    session_id: int
    integrity_score: int = Field(ge=0, le=100)
    status: str  # "clean", "needs_review", "flagged"
    total_events: int = Field(ge=0)
    event_counts_by_type: dict[str, int] = Field(default_factory=dict)
    event_counts_by_severity: dict[str, int] = Field(default_factory=dict)
    timeline: list[ProctoringTimelineItem] = Field(default_factory=list)
