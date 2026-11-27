from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview_blueprint import InterviewBlueprint
from app.models.interview_execution import InterviewExecutionSession
from app.models.interview_scorecard import InterviewScorecard
from app.models.learning_roadmap_db import LearningRoadmap, LearningRoadmapItem
from app.services.interview_execution_service import (
    InterviewExecutionSessionNotFoundError,
)


class InterviewRoadmapSyncService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def sync_gaps_to_roadmap(
        self,
        session_id: int,
    ) -> dict[str, int | str | list[str]]:
        session = self.db.get(InterviewExecutionSession, session_id)
        if session is None:
            raise InterviewExecutionSessionNotFoundError(
                f"Interview session {session_id} was not found."
            )

        blueprint = self.db.get(InterviewBlueprint, session.blueprint_id)
        if blueprint is None:
            raise ValueError(
                f"Blueprint {session.blueprint_id} was not found."
            )

        resume_id = blueprint.resume_id
        job_id = blueprint.job_id

        # 1. Get or create the LearningRoadmap
        stmt = select(LearningRoadmap).where(
            LearningRoadmap.resume_id == resume_id,
            LearningRoadmap.job_id == job_id,
        )
        roadmap = self.db.scalar(stmt)
        if roadmap is None:
            roadmap = LearningRoadmap(resume_id=resume_id, job_id=job_id)
            self.db.add(roadmap)
            self.db.flush()

        # 2. Extract weak competencies from scorecard or answer evaluations
        scorecard_stmt = select(InterviewScorecard).where(
            InterviewScorecard.session_id == session_id
        )
        scorecard = self.db.scalar(scorecard_stmt)

        candidate_gaps: set[str] = set()

        if scorecard and scorecard.improvement_areas:
            for item in scorecard.improvement_areas:
                if item and item.strip():
                    # Clean up sentences to concise competency phrases
                    cleaned = item.split(":")[0].split(".")[0].strip()
                    candidate_gaps.add(cleaned[:60])

        # Also pull low-scoring evaluated questions if any
        for evaluation in session.evaluations:
            if float(evaluation.weighted_score) < 3.2:
                candidate_gaps.add(evaluation.competency_reference.strip()[:60])

        if not candidate_gaps:
            # If all scored high, use any target competencies from blueprint
            for comp in blueprint.competencies[:2]:
                candidate_gaps.add(comp.name.strip()[:60])

        # 3. Add to roadmap items if not already present
        existing_items_stmt = select(LearningRoadmapItem.skill).where(
            LearningRoadmapItem.roadmap_id == roadmap.id
        )
        existing_skills = {
            s.lower() for s in self.db.scalars(existing_items_stmt).all()
        }

        added_skills: list[str] = []
        for gap in candidate_gaps:
            if not gap or gap.lower() in existing_skills:
                continue

            item = LearningRoadmapItem(
                roadmap_id=roadmap.id,
                skill=gap,
                skill_gap_status="missing",
                priority="high",
                reason=(
                    f"Identified as priority focus during AI Interview Session #{session_id} "
                    f"for {blueprint.target_role}."
                ),
                progress_status="not_started",
            )
            self.db.add(item)
            added_skills.append(gap)
            existing_skills.add(gap.lower())

        self.db.commit()

        return {
            "roadmap_id": roadmap.id,
            "session_id": session_id,
            "resume_id": resume_id,
            "job_id": job_id,
            "added_count": len(added_skills),
            "added_skills": added_skills,
        }
