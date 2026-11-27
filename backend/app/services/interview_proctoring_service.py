from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview_execution import InterviewExecutionSession
from app.models.interview_proctoring import (
    ProctoringEvent,
    ProctoringEventCreate,
    ProctoringEventResponse,
    ProctoringEventType,
    ProctoringSeverity,
    ProctoringSummaryResponse,
    ProctoringTimelineItem,
)
from app.services.interview_execution_service import (
    InterviewExecutionSessionNotFoundError,
)


EVENT_LABELS: dict[ProctoringEventType, str] = {
    ProctoringEventType.TAB_SWITCH: "Switched away from interview tab",
    ProctoringEventType.WINDOW_BLUR: "Window focus lost",
    ProctoringEventType.PASTE_DETECTED: "External text pasted into workspace",
    ProctoringEventType.NO_FACE: "Candidate face not detected in frame",
    ProctoringEventType.MULTIPLE_FACES: "Multiple individuals detected in frame",
    ProctoringEventType.AUDIO_ANOMALY: "Background voice or audio anomaly detected",
}


class InterviewProctoringService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _ensure_session_exists(self, session_id: int) -> InterviewExecutionSession:
        session = self.db.get(InterviewExecutionSession, session_id)
        if session is None:
            raise InterviewExecutionSessionNotFoundError(
                f"Interview session {session_id} was not found."
            )
        return session

    def record_event(
        self,
        session_id: int,
        payload: ProctoringEventCreate,
    ) -> ProctoringEventResponse:
        self._ensure_session_exists(session_id)

        event = ProctoringEvent(
            session_id=session_id,
            event_type=payload.event_type,
            severity=payload.severity,
            details=payload.details,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return ProctoringEventResponse.model_validate(event)

    def get_summary(self, session_id: int) -> ProctoringSummaryResponse:
        self._ensure_session_exists(session_id)

        events_stmt = (
            select(ProctoringEvent)
            .where(ProctoringEvent.session_id == session_id)
            .order_by(ProctoringEvent.timestamp.asc())
        )
        events = list(self.db.scalars(events_stmt).all())

        counts_by_type: dict[str, int] = {}
        counts_by_severity: dict[str, int] = {
            "low": 0,
            "medium": 0,
            "high": 0,
        }

        timeline: list[ProctoringTimelineItem] = []

        penalty = 0
        for event in events:
            ev_type = (
                event.event_type.value
                if hasattr(event.event_type, "value")
                else str(event.event_type)
            )
            ev_sev = (
                event.severity.value
                if hasattr(event.severity, "value")
                else str(event.severity)
            )

            counts_by_type[ev_type] = counts_by_type.get(ev_type, 0) + 1
            counts_by_severity[ev_sev] = counts_by_severity.get(ev_sev, 0) + 1

            if ev_sev == "low":
                penalty += 2
            elif ev_sev == "medium":
                penalty += 8
            elif ev_sev == "high":
                penalty += 15

            label = EVENT_LABELS.get(
                event.event_type,
                f"Integrity event: {ev_type.replace('_', ' ').capitalize()}",
            )

            timeline.append(
                ProctoringTimelineItem(
                    id=event.id,
                    event_type=ev_type,
                    severity=ev_sev,
                    timestamp=event.timestamp,
                    label=label,
                    details=event.details or {},
                )
            )

        integrity_score = max(0, 100 - penalty)
        if integrity_score >= 85:
            status = "clean"
        elif integrity_score >= 65:
            status = "needs_review"
        else:
            status = "flagged"

        return ProctoringSummaryResponse(
            session_id=session_id,
            integrity_score=integrity_score,
            status=status,
            total_events=len(events),
            event_counts_by_type=counts_by_type,
            event_counts_by_severity=counts_by_severity,
            timeline=timeline,
        )
