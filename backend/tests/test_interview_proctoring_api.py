from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.core.init_db  # noqa: F401
from app.api import interview_proctoring as api_module
from app.main import app
from app.models.interview_model_answer import DeliveryMetrics, ModelAnswerResponse
from app.models.interview_proctoring import (
    ProctoringEventCreate,
    ProctoringEventResponse,
    ProctoringEventType,
    ProctoringSeverity,
    ProctoringSummaryResponse,
)
from app.models.user import User


def test_api_record_proctoring_event(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "require_owned_execution_session",
        lambda session_id, user, db: None,
    )

    fake_response = ProctoringEventResponse(
        id=1,
        session_id=10,
        event_type=ProctoringEventType.TAB_SWITCH,
        severity=ProctoringSeverity.MEDIUM,
        timestamp="2026-11-25T00:00:00Z",
        details={"duration_ms": 1200},
    )

    class FakeService:
        def __init__(self, db):
            pass

        def record_event(self, session_id, payload):
            return fake_response

    monkeypatch.setattr(api_module, "InterviewProctoringService", FakeService)

    fake_user = User(id=1, email="candidate@careerlens.dev", name="Candidate")
    resp = api_module.record_proctoring_event(
        session_id=10,
        payload=ProctoringEventCreate(
            event_type=ProctoringEventType.TAB_SWITCH,
            severity=ProctoringSeverity.MEDIUM,
            details={"duration_ms": 1200},
        ),
        db=object(),
        current_user=fake_user,
    )

    assert resp.id == 1
    assert resp.event_type == ProctoringEventType.TAB_SWITCH


def test_api_get_proctoring_summary(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "require_owned_execution_session",
        lambda session_id, user, db: None,
    )

    fake_summary = ProctoringSummaryResponse(
        session_id=10,
        integrity_score=92,
        status="clean",
        total_events=1,
        event_counts_by_type={"tab_switch": 1},
        event_counts_by_severity={"medium": 1},
        timeline=[],
    )

    class FakeService:
        def __init__(self, db):
            pass

        def get_summary(self, session_id):
            return fake_summary

    monkeypatch.setattr(api_module, "InterviewProctoringService", FakeService)

    fake_user = User(id=1, email="candidate@careerlens.dev", name="Candidate")
    resp = api_module.get_proctoring_summary(
        session_id=10,
        db=object(),
        current_user=fake_user,
    )

    assert resp.integrity_score == 92
    assert resp.status == "clean"


def test_api_model_answer_comparison(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "require_owned_execution_session",
        lambda session_id, user, db: None,
    )

    fake_model = ModelAnswerResponse(
        question_id=101,
        question_text="How do you scale FastAPI?",
        target_competency="Backend Scaling",
        candidate_answer="I use horizontal workers and async I/O.",
        model_answer="Situation: ... Action: ... Result: ...",
        missing_critical_nuances=["Connection pooling"],
        key_strengths_demonstrated=["Clear async foundation"],
        delivery_metrics=DeliveryMetrics(
            wpm=130,
            word_count=8,
            filler_word_count=0,
            filler_words_detected=[],
            pacing_rating="optimal",
            clarity_score=9.5,
        ),
    )

    class FakeModelService:
        def __init__(self, db):
            pass

        def generate_for_answer(self, session_id, answer_id, duration_seconds=None):
            return fake_model

    monkeypatch.setattr(api_module, "InterviewModelAnswerService", FakeModelService)

    fake_user = User(id=1, email="candidate@careerlens.dev", name="Candidate")
    resp = api_module.get_model_answer_comparison(
        session_id=10,
        answer_id=201,
        duration_seconds=15.0,
        db=object(),
        current_user=fake_user,
    )

    assert resp.question_id == 101
    assert "Situation" in resp.model_answer
    assert resp.delivery_metrics.wpm == 130


def test_api_sync_roadmap(monkeypatch):
    monkeypatch.setattr(
        api_module,
        "require_owned_execution_session",
        lambda session_id, user, db: None,
    )

    class FakeSyncService:
        def __init__(self, db):
            pass

        def sync_gaps_to_roadmap(self, session_id):
            return {
                "roadmap_id": 5,
                "session_id": session_id,
                "added_count": 2,
                "added_skills": ["Database Connection Pooling"],
            }

    monkeypatch.setattr(api_module, "InterviewRoadmapSyncService", FakeSyncService)

    fake_user = User(id=1, email="candidate@careerlens.dev", name="Candidate")
    resp = api_module.sync_interview_gaps_to_roadmap(
        session_id=10,
        db=object(),
        current_user=fake_user,
    )

    assert resp["roadmap_id"] == 5
    assert resp["added_count"] == 2


def test_api_enforces_auth_ownership(monkeypatch):
    def fake_require_owned(session_id, user, db):
        raise HTTPException(status_code=403, detail="Forbidden session access")

    monkeypatch.setattr(api_module, "require_owned_execution_session", fake_require_owned)

    fake_user = User(id=2, email="other@careerlens.dev", name="Other")

    with pytest.raises(HTTPException) as exc_info:
        api_module.get_proctoring_summary(
            session_id=10,
            db=object(),
            current_user=fake_user,
        )

    assert exc_info.value.status_code == 403
