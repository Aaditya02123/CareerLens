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
    },
    "projects": {
        "projects",
        "academic projects",
    },
    "certifications": {
        "certifications",
        "certificates",
    },
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


def _heading_for(line: str) -> str | None:
    """Return the section name if the line is a recognized heading."""
    normalized_line = re.sub(r"[:\s]+$", "", line).strip().lower()

    for section_name, headings in SECTION_HEADINGS.items():
        if normalized_line in headings:
            return section_name

    return None


def _extract_sections(lines: list[str]) -> dict[str, list[str]]:
    """Collect lines under each recognized section heading."""
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


def _split_skills(lines: list[str]) -> list[str]:
    """Split obvious comma, pipe, and bullet-separated skill values."""
    skills = []

    for line in lines:
        cleaned_line = _clean_entry(line)

        for skill in re.split(r"[,|•]", cleaned_line):
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