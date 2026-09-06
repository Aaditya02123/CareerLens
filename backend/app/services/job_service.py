from sqlalchemy.orm import Session

from app.models.jobs import Job, JobCreate
from app.repositories.job_repository import JobRepository


class JobNotFoundError(LookupError):
    """Raised when a requested job does not exist."""


class JobService:
    """Business logic for jobs."""

    def __init__(self, session: Session) -> None:
        self.repository = JobRepository(session)

    def create_job(self, job_data: JobCreate) -> Job:
        """Create a job through the repository."""
        if not job_data.title.strip():
            raise ValueError("Job title cannot be empty.")

        if not job_data.description.strip():
            raise ValueError("Job description cannot be empty.")

        if not job_data.source.strip():
            raise ValueError("Job source cannot be empty.")

        return self.repository.create(
            title=job_data.title,
            company=job_data.company,
            description=job_data.description,
            responsibilities=job_data.responsibilities,
            required_skills=job_data.required_skills,
            preferred_skills=job_data.preferred_skills,
            experience_level=job_data.experience_level,
            location=job_data.location,
            source=job_data.source,
            source_job_id=job_data.source_job_id,
            source_url=job_data.source_url,
        )

    def get_job(self, job_id: int) -> Job:
        """Return a job or raise a domain-level not-found error."""
        job = self.repository.get_by_id(job_id)

        if job is None:
            raise JobNotFoundError("The requested job was not found.")

        return job

    def list_jobs(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """Return a page of jobs."""
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100.")

        if offset < 0:
            raise ValueError("Offset cannot be negative.")

        return self.repository.list_jobs(
            limit=limit,
            offset=offset,
        )