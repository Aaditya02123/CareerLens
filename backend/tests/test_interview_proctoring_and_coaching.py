from __future__ import annotations

from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "TEXT"

import app.core.init_db  # noqa: F401
from app.core.database import Base
from app.models.interview_blueprint import (
    BlueprintCompetency,
    BlueprintQuestion,
    InterviewBlueprint,
)
from app.models.interview_execution import (
    InterviewExecutionSession,
    InterviewExecutionStatus,
    InterviewSessionAnswer,
    InterviewSessionQuestion,
)
from app.models.interview_proctoring import (
    ProctoringEventCreate,
    ProctoringEventType,
    ProctoringSeverity,
)
from app.models.interview_scorecard import (
    InterviewAnswerEvaluation,
    InterviewScorecard,
    ScorecardStatus,
)
from app.models.jobs import Job
from app.models.learning_roadmap_db import LearningRoadmap, LearningRoadmapItem
from app.models.resume import Resume
from app.models.user import User
from app.services.interview_model_answer_service import (
    InterviewModelAnswerService,
    calculate_delivery_metrics,
)
from app.services.interview_proctoring_service import InterviewProctoringService
from app.services.interview_roadmap_service import InterviewRoadmapSyncService


def test_calculate_delivery_metrics():
    sample_text = (
        "Well, um, basically I like designed the backend architecture using FastAPI, "
        "and you know, actually we achieved high throughput."
    )
    metrics = calculate_delivery_metrics(sample_text, duration_seconds=10.0)

    assert metrics.word_count > 10
    assert metrics.filler_word_count >= 4
    assert "um" in metrics.filler_words_detected
    assert "basically" in metrics.filler_words_detected
    assert metrics.wpm > 50
    assert 4.0 <= metrics.clarity_score <= 10.0


@pytest.fixture
def memory_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Create required tables for execution and proctoring
    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            Job.__table__,
            Resume.__table__,
            InterviewBlueprint.__table__,
            BlueprintCompetency.__table__,
            BlueprintQuestion.__table__,
            InterviewExecutionSession.__table__,
            InterviewSessionQuestion.__table__,
            InterviewSessionAnswer.__table__,
            InterviewAnswerEvaluation.__table__,
            InterviewScorecard.__table__,
            LearningRoadmap.__table__,
            LearningRoadmapItem.__table__,
        ],
    )
    # Create SQLite-compatible proctoring table manually if enum mismatch
    from app.models.interview_proctoring import ProctoringEvent
    ProctoringEvent.__table__.create(bind=engine)

    SessionClass = sessionmaker(bind=engine)
    session = SessionClass()

    # Seed User, Job, Resume, Blueprint, ExecutionSession
    user = User(id=1, email="candidate@careerlens.dev", name="Candidate")
    job = Job(
        id=1,
        title="Backend Engineer",
        company="TechCorp",
        description="FastAPI dev",
        source="manual",
    )
    resume = Resume(
        id=1,
        user_id=1,
        original_filename="resume.pdf",
        stored_filename="stored.pdf",
        content_type="application/pdf",
    )
    blueprint = InterviewBlueprint(
        id=1,
        resume_id=1,
        job_id=1,
        target_role="Backend Engineer",
        interview_type="technical",
        difficulty="medium",
        duration_minutes=30,
        question_count=1,
    )
    comp = BlueprintCompetency(
        id=1,
        blueprint_id=1,
        name="API Architecture",
        description="Design clean APIs",
        category="technical",
        weight_percent=100,
    )
    exec_session = InterviewExecutionSession(
        id=10,
        blueprint_id=1,
        status=InterviewExecutionStatus.IN_PROGRESS,
        total_questions=1,
        answered_questions=0,
    )
    q = InterviewSessionQuestion(
        id=101,
        session_id=10,
        question_order=1,
        conversation_order=1.0,
        question="How do you handle API concurrency and idempotency?",
        question_category="technical",
        difficulty="medium",
        target_competency="API Architecture",
        assessment_objective="Evaluate concurrency controls and idempotent request handling",
        relevance_reason="Core backend requirement",
    )
    ans = InterviewSessionAnswer(
        id=201,
        session_id=10,
        session_question_id=101,
        question_order=1,
        conversation_order=1.0,
        answer="I use unique idempotency keys in Redis and database row locking to prevent duplicate writes.",
    )

    session.add_all([user, job, resume, blueprint, comp, exec_session, q, ans])
    session.commit()

    yield session
    session.close()


def test_proctoring_service_records_and_computes_integrity_score(memory_db):
    service = InterviewProctoringService(memory_db)

    # 1. Clean session start
    initial_summary = service.get_summary(10)
    assert initial_summary.integrity_score == 100
    assert initial_summary.status == "clean"
    assert initial_summary.total_events == 0

    # 2. Record tab switch (medium severity)
    ev1 = service.record_event(
        10,
        ProctoringEventCreate(
            event_type=ProctoringEventType.TAB_SWITCH,
            severity=ProctoringSeverity.MEDIUM,
            details={"duration_ms": 3500},
        ),
    )
    assert ev1.id is not None
    assert ev1.event_type == ProctoringEventType.TAB_SWITCH

    # 3. Record paste (high severity)
    service.record_event(
        10,
        ProctoringEventCreate(
            event_type=ProctoringEventType.PASTE_DETECTED,
            severity=ProctoringSeverity.HIGH,
            details={"characters": 450},
        ),
    )

    summary = service.get_summary(10)
    # 100 - 8 (medium) - 15 (high) = 77
    assert summary.integrity_score == 77
    assert summary.status == "needs_review"
    assert summary.total_events == 2
    assert summary.event_counts_by_type["tab_switch"] == 1
    assert summary.event_counts_by_type["paste_detected"] == 1
    assert len(summary.timeline) == 2


def test_model_answer_service_generates_grounded_comparison(memory_db):
    service = InterviewModelAnswerService(memory_db)
    result = service.generate_for_answer(session_id=10, answer_id=201)

    assert result.question_id == 101
    assert "concurrency" in result.question_text.lower()
    assert "Situation & Task" in result.model_answer
    assert "Action" in result.model_answer
    assert "Result" in result.model_answer
    assert len(result.missing_critical_nuances) > 0
    assert len(result.key_strengths_demonstrated) > 0
    assert result.delivery_metrics.word_count > 5


def test_roadmap_sync_service_provisions_gaps(memory_db):
    # Add a scorecard with improvement areas
    scorecard = InterviewScorecard(
        id=1,
        session_id=10,
        status=ScorecardStatus.COMPLETE,
        overall_score=2.8,
        strengths=["Quick response time"],
        improvement_areas=["Distributed Lock Timeout Handling", "Database Connection Pooling"],
    )
    memory_db.add(scorecard)
    memory_db.commit()

    sync_service = InterviewRoadmapSyncService(memory_db)
    result = sync_service.sync_gaps_to_roadmap(10)

    assert result["added_count"] >= 1
    assert "Distributed Lock Timeout Handling" in result["added_skills"]
    assert result["resume_id"] == 1
    assert result["job_id"] == 1
