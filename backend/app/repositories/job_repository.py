from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.jobs import Job


class JobRepository:
    """Database operations for the Job model."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        title: str,
        company: str | None,
        description: str,
        responsibilities: list[str],
        required_skills: list[str],
        preferred_skills: list[str],
        experience_level: str | None,
        location: str | None,
        source: str,
        source_job_id: str | None,
        source_url: str | None,
    ) -> Job:
        """Create and persist a job posting."""
        job = Job(
            title=title,
            company=company,
            description=description,
            responsibilities=responsibilities,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            experience_level=experience_level,
            location=location,
            source=source,
            source_job_id=source_job_id,
            source_url=source_url,
        )

        self.session.add(job)

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise

        self.session.refresh(job)
        return job

    def get_by_id(self, job_id: int) -> Job | None:
        """Return a job by ID, if one exists."""
        statement = select(Job).where(Job.id == job_id)
        return self.session.scalar(statement)

    def get_by_source_job_id(
        self,
        source: str,
        source_job_id: str,
    ) -> Job | None:
        """Return a job by its source-specific identifier."""
        statement = select(Job).where(
            Job.source == source,
            Job.source_job_id == source_job_id,
        )
        return self.session.scalar(statement)

    def list_jobs(
        self,
        limit: int,
        offset: int,
    ) -> list[Job]:
        """Return jobs using simple limit and offset pagination."""
        statement = (
            select(Job)
            .order_by(Job.created_at.desc(), Job.id.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(self.session.scalars(statement).all())