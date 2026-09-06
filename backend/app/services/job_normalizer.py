from dataclasses import dataclass
import re

from app.models.jobs import JobCreate


WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class NormalizedJobData:
    """Normalized values ready for persistence."""

    title: str
    company: str | None
    description: str
    responsibilities: list[str]
    required_skills: list[str]
    preferred_skills: list[str]
    experience_level: str | None
    location: str | None
    source: str
    source_job_id: str | None
    source_url: str | None


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = WHITESPACE_PATTERN.sub(" ", value).strip()
    return cleaned or None


def normalize_comparison_value(value: str | None) -> str | None:
    """Return a case-insensitive comparison representation."""
    cleaned = _clean_text(value)
    return cleaned.casefold() if cleaned else None


def _normalize_list(items: list[str]) -> list[str]:
    normalized_items: list[str] = []
    seen: set[str] = set()

    for item in items:
        cleaned_item = _clean_text(item)

        if not cleaned_item:
            continue

        comparison_value = cleaned_item.casefold()

        if comparison_value in seen:
            continue

        seen.add(comparison_value)
        normalized_items.append(cleaned_item)

    return normalized_items


def _normalize_experience_level(value: str | None) -> str | None:
    cleaned = _clean_text(value)

    if cleaned is None:
        return None

    normalized = cleaned.casefold()

    variants = {
        "fresher": "entry-level",
        "freshers": "entry-level",
        "entry level": "entry-level",
        "entry-level": "entry-level",
        "junior": "junior",
        "mid level": "mid-level",
        "mid-level": "mid-level",
        "senior": "senior",
        "senior level": "senior-level",
        "senior-level": "senior-level",
    }

    return variants.get(normalized, normalized)


def normalize_job_data(job_data: JobCreate) -> NormalizedJobData:
    """Normalize job input deterministically before persistence."""
    return NormalizedJobData(
        title=_clean_text(job_data.title) or "",
        company=_clean_text(job_data.company),
        description=_clean_text(job_data.description) or "",
        responsibilities=_normalize_list(job_data.responsibilities),
        required_skills=_normalize_list(job_data.required_skills),
        preferred_skills=_normalize_list(job_data.preferred_skills),
        experience_level=_normalize_experience_level(
            job_data.experience_level
        ),
        location=_clean_text(job_data.location),
        source=(
            normalize_comparison_value(job_data.source)
            or ""
        ),
        source_job_id=_clean_text(job_data.source_job_id),
        source_url=_clean_text(job_data.source_url),
    )