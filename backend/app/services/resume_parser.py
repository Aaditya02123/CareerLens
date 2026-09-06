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
        projects=[
            _clean_entry(line)
            for line in sections["projects"]
            if _clean_entry(line)
        ],
        certifications=[
            _clean_entry(line)
            for line in sections["certifications"]
            if _clean_entry(line)
        ],
    )