from sqlalchemy.orm import Session

from app.models.jobs import Job, JobCreate
from app.repositories.job_repository import JobRepository
from app.services.job_duplicate_detector import JobDuplicateDetector
from app.services.job_normalizer import normalize_job_data


class JobNotFoundError(LookupError):
    """Raised when a requested job does not exist."""


class JobDuplicateError(RuntimeError):
    """Raised when a job appears to duplicate an existing record."""


class JobService:
    """Business logic for jobs."""

    def __init__(self, session: Session) -> None:
        self.repository = JobRepository(session)
        self.duplicate_detector = JobDuplicateDetector(self.repository)

    def create_job(self, job_data: JobCreate) -> Job:
        """Normalize, check, and persist a job posting."""
        if not job_data.title.strip():
            raise ValueError("Job title cannot be empty.")

        if not job_data.description.strip():
            raise ValueError("Job description cannot be empty.")

        if not job_data.source.strip():
            raise ValueError("Job source cannot be empty.")

        normalized_data = normalize_job_data(job_data)
        duplicate_match = self.duplicate_detector.find_duplicate(
            normalized_data
        )

        if duplicate_match is not None:
            raise JobDuplicateError(duplicate_match.reason)

        return self.repository.create(
            title=normalized_data.title,
            company=normalized_data.company,
            description=normalized_data.description,
            responsibilities=normalized_data.responsibilities,
            required_skills=normalized_data.required_skills,
            preferred_skills=normalized_data.preferred_skills,
            experience_level=normalized_data.experience_level,
            location=normalized_data.location,
            source=normalized_data.source,
            source_job_id=normalized_data.source_job_id,
            source_url=normalized_data.source_url,
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