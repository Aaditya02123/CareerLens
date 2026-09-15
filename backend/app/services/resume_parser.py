import re

from app.models.resume import StructuredResume


SECTION_HEADINGS = {
    "skills": {
        "skills",
        "technical skills",
    },
    "education": {
        "education",
        "academic background",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "internship",
        "internships",
    },
    "projects": {
        "projects",
        "academic projects",
    },
    "certifications": {
        "certifications",
        "certificates",
        "certifications & achievements",
        "achievements",
    },
}

SKILL_SUBSECTION_LABELS = {
    "languages",
    "frameworks/libraries",
    "frameworks",
    "libraries",
    "databases",
    "ai/tools",
    "ai",
    "tools",
    "core cs",
}

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PROJECT_SEPARATOR_PATTERN = re.compile(r"\s+[—–-]\s+")
PROJECT_SENTENCE_START_PATTERN = re.compile(
    r"^(?:a|an|built|created|designed|developed|implemented|"
    r"improved|reduced|used|using|worked|led|developing)\b",
    flags=re.IGNORECASE,
)


def _normalize_lines(text: str) -> list[str]:
    """Strip surrounding whitespace and ignore empty lines."""
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def _normalize_heading(line: str) -> str:
    """Normalize a possible heading for case-insensitive comparison."""
    return re.sub(r"[:\s]+$", "", line).strip().lower()


def _heading_for(line: str) -> str | None:
    """Return the section name if the line is an exact recognized heading."""
    normalized_line = _normalize_heading(line)

    for section_name, headings in SECTION_HEADINGS.items():
        if normalized_line in headings:
            return section_name

    return None


def _extract_sections(lines: list[str]) -> dict[str, list[str]]:
    """Collect lines under each recognized top-level section heading."""
    sections = {
        "skills": [],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
    }
    current_section: str | None = None

    for line in lines:
        heading = _heading_for(line)

        if heading is not None:
            current_section = heading
            continue

        if current_section is not None:
            sections[current_section].append(line)

    return sections


def _clean_entry(line: str) -> str:
    """Remove common list markers from a section entry."""
    return re.sub(r"^\s*(?:[-*•]\s*)+", "", line).strip()


def _normalize_skill_subsection_label(label: str) -> str:
    """Normalize spacing and case in a skill subsection label."""
    normalized_label = re.sub(r"\s*/\s*", "/", label.strip().lower())
    return re.sub(r"\s+", " ", normalized_label)


def _remove_skill_subsection_label(line: str) -> str:
    """Remove a known skill subsection label before its values."""
    cleaned_line = _clean_entry(line)
    label, separator, values = cleaned_line.partition(":")

    normalized_label = _normalize_skill_subsection_label(label)

    if separator and normalized_label in SKILL_SUBSECTION_LABELS:
        return values.strip()

    return cleaned_line


def _split_skills(lines: list[str]) -> list[str]:
    """Split skill subsections and their comma- or bullet-separated values."""
    skills = []

    for line in lines:
        for subsection in line.split("|"):
            skill_values = _remove_skill_subsection_label(subsection)

            if not skill_values:
                continue

            for skill in re.split(r"[,•]", skill_values):
                cleaned_skill = _clean_entry(skill)

                if cleaned_skill:
                    skills.append(cleaned_skill)

    return skills


def _looks_like_project_start(line: str) -> bool:
    """
    Detect a strong project-heading structure.

    URLs, normal description sentences, and arbitrary pipe characters
    are not treated as project boundaries.
    """
    cleaned_line = _clean_entry(line)

    if not cleaned_line:
        return False

    if re.match(r"^project\s*:", cleaned_line, flags=re.IGNORECASE):
        return True

    if cleaned_line.lower().startswith(
        ("http://", "https://", "www.")
    ):
        return False

    if cleaned_line.startswith("[") and "](" in cleaned_line:
        return False

    if cleaned_line.endswith((".", "!", "?")):
        return False

    if PROJECT_SENTENCE_START_PATTERN.match(cleaned_line):
        return False

    separator_match = PROJECT_SEPARATOR_PATTERN.search(cleaned_line)

    if "|" in cleaned_line:
        title_part, technology_part = cleaned_line.split(
            "|",
            maxsplit=1,
        )

        title_part = title_part.strip()
        technology_part = technology_part.strip()

        if not title_part or not technology_part:
            return False

        if len(title_part) > 100 or len(technology_part) > 120:
            return False

        has_title_separator = (
            separator_match is not None
            or ":" in title_part
        )
        has_technology_structure = (
            "," in technology_part
            or "/" in technology_part
            or len(technology_part.split()) <= 8
        )

        return has_title_separator and has_technology_structure

    if separator_match is not None:
        title_part, details_part = re.split(
            PROJECT_SEPARATOR_PATTERN,
            cleaned_line,
            maxsplit=1,
        )

        return (
            1 <= len(title_part.strip()) <= 80
            and 1 <= len(details_part.strip()) <= 100
        )

    return False


def _group_projects(lines: list[str]) -> list[str]:
    """
    Group consecutive lines belonging to structured project headings.

    If no strong project-heading signal is present, preserve the previous
    one-line-per-entry behavior.
    """
    cleaned_lines = [
        _clean_entry(line)
        for line in lines
        if _clean_entry(line)
    ]

    if not any(
        _looks_like_project_start(line)
        for line in cleaned_lines
    ):
        return cleaned_lines

    projects: list[str] = []
    current_project: list[str] = []

    for line in cleaned_lines:
        if (
            _looks_like_project_start(line)
            and current_project
        ):
            projects.append(" ".join(current_project))
            current_project = []

        current_project.append(line)

    if current_project:
        projects.append(" ".join(current_project))

    return projects


def _extract_email(text: str) -> str | None:
    """Return the first email address found in the resume text."""
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def _looks_like_name(line: str) -> bool:
    """Apply a conservative heuristic for a name near the resume start."""
    if not 2 <= len(line) <= 60:
        return False

    if "@" in line or "://" in line or ":" in line:
        return False

    if any(character.isdigit() for character in line):
        return False

    words = line.split()
    return 1 <= len(words) <= 5


def _extract_name(lines: list[str]) -> str | None:
    """Use the first plausible pre-section line as the candidate's name."""
    for line in lines[:5]:
        if _heading_for(line) is not None:
            break

        cleaned_line = _clean_entry(line)

        if _looks_like_name(cleaned_line):
            return cleaned_line

    return None


def parse_resume_text(text: str) -> StructuredResume:
    """Parse raw resume text into a simple structured representation."""
    lines = _normalize_lines(text)
    sections = _extract_sections(lines)

    return StructuredResume(
        name=_extract_name(lines),
        email=_extract_email(text),
        skills=_split_skills(sections["skills"]),
        education=[
            _clean_entry(line)
            for line in sections["education"]
            if _clean_entry(line)
        ],
        experience=[
            _clean_entry(line)
            for line in sections["experience"]
            if _clean_entry(line)
        ],
        projects=_group_projects(sections["projects"]),
        certifications=[
            _clean_entry(line)
            for line in sections["certifications"]
            if _clean_entry(line)
        ],
    )