from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.resume_analysis import ResumeAnalysis


class ResumeAnalysisRepository:
    """Database operations for persisted resume analyses."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        resume_id: int,
        structured_resume: dict,
        categorized_skills: dict,
    ) -> ResumeAnalysis:
        """Create and persist a resume analysis."""
        analysis = ResumeAnalysis(
            resume_id=resume_id,
            structured_resume=structured_resume,
            categorized_skills=categorized_skills,
        )

        self.session.add(analysis)

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

        self.session.refresh(analysis)
        return analysis

    def get_by_resume_id(
        self,
        resume_id: int,
    ) -> ResumeAnalysis | None:
        """Return the analysis for a resume, if one exists."""
        statement = select(ResumeAnalysis).where(
            ResumeAnalysis.resume_id == resume_id
        )
        return self.session.scalar(statement)

    def update(
        self,
        analysis: ResumeAnalysis,
        structured_resume: dict,
        categorized_skills: dict,
    ) -> ResumeAnalysis:
        """Replace the stored analysis data for a resume."""
        analysis.structured_resume = structured_resume
        analysis.categorized_skills = categorized_skills

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

        self.session.refresh(analysis)
        return analysis