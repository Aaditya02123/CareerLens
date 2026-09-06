from dataclasses import dataclass
import re

from app.models.jobs import Job
from app.repositories.job_repository import JobRepository
from app.services.job_normalizer import (
    NormalizedJobData,
    normalize_comparison_value,
)


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "will",
    "you",
    "your",
}

DESCRIPTION_TOKEN_PATTERN = re.compile(r"[a-z0-9+#.]{3,}")


@dataclass(frozen=True)
class DuplicateMatch:
    """Explain why an existing job was considered a duplicate."""

    job: Job
    reason: str


def _skill_set(
    required_skills: list[str],
    preferred_skills: list[str],
) -> set[str]:
    return {
        skill.casefold().strip()
        for skill in [*required_skills, *preferred_skills]
        if skill.strip()
    }


def _description_tokens(description: str) -> set[str]:
    return {
        token
        for token in DESCRIPTION_TOKEN_PATTERN.findall(
            description.casefold()
        )
        if token not in STOPWORDS
    }


def _has_conservative_skill_overlap(
    incoming: NormalizedJobData,
    existing: Job,
) -> bool:
    incoming_skills = _skill_set(
        incoming.required_skills,
        incoming.preferred_skills,
    )
    existing_skills = _skill_set(
        existing.required_skills,
        existing.preferred_skills,
    )

    if not incoming_skills or not existing_skills:
        return False

    shared_skills = incoming_skills & existing_skills
    smaller_skill_count = min(
        len(incoming_skills),
        len(existing_skills),
    )

    if len(shared_skills) < 2:
        return False

    overlap_ratio = len(shared_skills) / smaller_skill_count
    return overlap_ratio >= 0.5


def _has_conservative_description_overlap(
    incoming: NormalizedJobData,
    existing: Job,
) -> bool:
    incoming_tokens = _description_tokens(incoming.description)
    existing_tokens = _description_tokens(existing.description)

    if not incoming_tokens or not existing_tokens:
        return False

    shared_tokens = incoming_tokens & existing_tokens
    union_tokens = incoming_tokens | existing_tokens

    if len(shared_tokens) < 5:
        return False

    jaccard_similarity = len(shared_tokens) / len(union_tokens)
    return jaccard_similarity >= 0.5


class JobDuplicateDetector:
    """Deterministically identify likely duplicate job records."""

    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    def find_duplicate(
        self,
        job_data: NormalizedJobData,
    ) -> DuplicateMatch | None:
        """Return a duplicate match with an explanation, if found."""
        if job_data.source_job_id is not None:
            exact_match = self.repository.get_by_source_job_id(
                source=job_data.source,
                source_job_id=job_data.source_job_id,
            )

            if exact_match is not None:
                return DuplicateMatch(
                    job=exact_match,
                    reason="The source and source job ID already exist.",
                )

        candidates = self.repository.find_candidates(
            title=job_data.title,
            company=job_data.company,
            location=job_data.location,
        )

        incoming_company = normalize_comparison_value(job_data.company)
        incoming_location = normalize_comparison_value(job_data.location)

        for candidate in candidates:
            candidate_company = normalize_comparison_value(
                candidate.company
            )
            candidate_location = normalize_comparison_value(
                candidate.location
            )

            if (
                incoming_company
                and candidate_company
                and incoming_company != candidate_company
            ):
                continue

            if (
                incoming_location
                and candidate_location
                and incoming_location != candidate_location
            ):
                continue

            has_skill_overlap = _has_conservative_skill_overlap(
                job_data,
                candidate,
            )
            has_description_overlap = _has_conservative_description_overlap(
                job_data,
                candidate,
            )

            if has_skill_overlap or has_description_overlap:
                return DuplicateMatch(
                    job=candidate,
                    reason=(
                        "The normalized title and substantial job details "
                        "match an existing job."
                    ),
                )

        return None