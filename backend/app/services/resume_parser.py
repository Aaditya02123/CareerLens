from __future__ import annotations

import re

from app.models.resume import (
    CredentialEntry,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    ResumeEntry,
    ResumeSection,
    StructuredResume,
)


# ============================================================================
# Section detection
# ============================================================================

SECTION_ALIASES: dict[str, set[str]] = {
    "summary": {
        "summary",
        "professional summary",
        "profile",
        "professional profile",
        "career summary",
        "objective",
        "career objective",
        "about me",
    },
    "skills": {
        "skills",
        "technical skills",
        "technical expertise",
        "key skills",
        "core skills",
        "competencies",
        "technical competencies",
    },
    "education": {
        "education",
        "academic background",
        "academic qualifications",
        "educational background",
        "qualifications",
        "academic history",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "career history",
        "internship",
        "internships",
        "professional experience & internships",
    },
    "projects": {
        "projects",
        "academic projects",
        "personal projects",
        "key projects",
        "selected projects",
        "technical projects",
        "project experience",
    },
    "certifications": {
        "certifications",
        "certificates",
        "licenses & certifications",
        "certifications & achievements",
        "certifications and achievements",
    },
    "training": {
        "training",
        "trainings",
        "courses",
        "coursework",
        "workshops",
        "seminars",
        "seminars & trainings",
        "seminars / trainings / workshops",
    },
    "achievements": {
        "achievements",
        "accomplishments",
        "honors",
        "honours",
        "awards",
    },
    "research": {
        "research",
        "research experience",
        "research projects",
    },
    "publications": {
        "publications",
        "papers",
        "research publications",
    },
    "volunteering": {
        "volunteering",
        "volunteer experience",
        "community involvement",
    },
    "leadership": {
        "leadership",
        "leadership experience",
        "positions of responsibility",
    },
    "interests": {
        "interests",
        "personal interests",
        "hobbies",
        "personal interests / hobbies",
    },
    "languages": {
        "languages",
        "language proficiency",
    },
}


SECTION_TITLES = {
    canonical: aliases
    for canonical, aliases in SECTION_ALIASES.items()
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
    "core computer science",
}


# ============================================================================
# Patterns
# ============================================================================

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

URL_PATTERN = re.compile(
    r"(?:"
    r"https?://[^\s|]+"
    r"|"
    r"www\.[^\s|]+"
    r"|"
    r"(?:github\.com|linkedin\.com)/[^\s|]+"
    r"|"
    r"(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}"
    r")",
    flags=re.IGNORECASE,
)

DATE_RANGE_PATTERN = re.compile(
    r"(?P<start>"
    r"(?:"
    r"Jan(?:uary)?|"
    r"Feb(?:ruary)?|"
    r"Mar(?:ch)?|"
    r"Apr(?:il)?|"
    r"May|"
    r"Jun(?:e)?|"
    r"Jul(?:y)?|"
    r"Aug(?:ust)?|"
    r"Sep(?:tember)?|"
    r"Oct(?:ober)?|"
    r"Nov(?:ember)?|"
    r"Dec(?:ember)?"
    r")"
    r"(?:\s+\d{4})?"
    r"|"
    r"\d{1,2}[/-]\d{4}"
    r"|"
    r"\d{4}"
    r")"
    r"\s*(?:[-–—]|to)\s*"
    r"(?P<end>"
    r"(?:"
    r"Present|"
    r"Current|"
    r"Now|"
    r"Jan(?:uary)?|"
    r"Feb(?:ruary)?|"
    r"Mar(?:ch)?|"
    r"Apr(?:il)?|"
    r"May|"
    r"Jun(?:e)?|"
    r"Jul(?:y)?|"
    r"Aug(?:ust)?|"
    r"Sep(?:tember)?|"
    r"Oct(?:ober)?|"
    r"Nov(?:ember)?|"
    r"Dec(?:ember)?"
    r")"
    r"(?:\s+\d{4})?"
    r"|"
    r"\d{1,2}[/-]\d{4}"
    r"|"
    r"\d{4}"
    r")",
    flags=re.IGNORECASE,
)

EXPECTED_DATE_PATTERN = re.compile(
    r"\bexpected\s+"
    r"(?P<date>"
    r"(?:"
    r"Jan(?:uary)?|"
    r"Feb(?:ruary)?|"
    r"Mar(?:ch)?|"
    r"Apr(?:il)?|"
    r"May|"
    r"Jun(?:e)?|"
    r"Jul(?:y)?|"
    r"Aug(?:ust)?|"
    r"Sep(?:tember)?|"
    r"Oct(?:ober)?|"
    r"Nov(?:ember)?|"
    r"Dec(?:ember)?"
    r")"
    r"(?:\s+\d{4})?"
    r"|"
    r"\d{4}"
    r")\b",
    flags=re.IGNORECASE,
)

GPA_PATTERN = re.compile(
    r"\b(?:gpa|cgpa)\s*[:=]?\s*"
    r"(?P<value>\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)\b",
    flags=re.IGNORECASE,
)

BULLET_PATTERN = re.compile(
    r"^\s*(?:[-*•▪◦●‣]\s+)"
)

PROJECT_SPLIT_PATTERN = re.compile(
    r"\s*[|]\s*"
)

PROJECT_DASH_PATTERN = re.compile(
    r"\s+[—–-]\s+"
)

SENTENCE_START_PATTERN = re.compile(
    r"^(?:a|an|the|built|created|designed|developed|implemented|"
    r"improved|integrated|delivered|used|using|worked|led|"
    r"evaluated|clarified|configured|migrated|deployed|"
    r"developing|responsible|managed|engineered|"
    r"contributed|implemented)\b",
    flags=re.IGNORECASE,
)

DEGREE_PATTERN = re.compile(
    r"\b("
    r"B\.?\s*Tech|"
    r"B\.?\s*E\.?|"
    r"M\.?\s*Tech|"
    r"M\.?\s*E\.?|"
    r"M\.?\s*S\.?|"
    r"B\.?\s*S\.?|"
    r"MCA|"
    r"BCA|"
    r"Ph\.?D\.?|"
    r"Master(?:'s)?|"
    r"Bachelor(?:'s)?|"
    r"Doctor(?:ate)?"
    r")\b",
    flags=re.IGNORECASE,
)


# ============================================================================
# Basic normalization
# ============================================================================

def _normalize_lines(text: str) -> list[str]:
    """
    Normalize extracted PDF text.

    We intentionally preserve meaningful line boundaries. PDF extraction
    frequently gives us already-separated semantic lines, so aggressively
    merging everything would make entity reconstruction harder.
    """
    normalized: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.replace("\xa0", " ").strip()

        if not line:
            continue

        line = re.sub(r"[ \t]+", " ", line)
        normalized.append(line)

    return normalized


def _clean_entry(line: str) -> str:
    """Remove common list markers and surrounding whitespace."""
    cleaned = BULLET_PATTERN.sub("", line)
    cleaned = re.sub(r"^\s*(?:[-*•▪◦●‣])\s*", "", cleaned)

    return cleaned.strip()

def _merge_wrapped_bullets(content: list[str]) -> list[str]:
    """Reconstruct bullet points that were split across PDF lines."""
    result: list[str] = []
    current_bullet: str | None = None

    for raw_line in content:
        line = raw_line.strip()

        if not line:
            continue

        if BULLET_PATTERN.match(line):
            if current_bullet is not None:
                result.append(current_bullet)

            current_bullet = _clean_entry(line)
            continue

        if current_bullet is not None:
            current_bullet = f"{current_bullet} {_clean_entry(line)}"
        else:
            result.append(_clean_entry(line))

    if current_bullet is not None:
        result.append(current_bullet)

    return [line.strip() for line in result if line and line.strip()]


def _normalize_heading(line: str) -> str:
    """Normalize a candidate section heading."""
    cleaned = _clean_entry(line)

    cleaned = cleaned.replace("&", " and ")
    cleaned = re.sub(r"[/|]+", " ", cleaned)
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned.strip().lower()


# ============================================================================
# Section detection
# ============================================================================

def _heading_for(line: str) -> str | None:
    """
    Return a canonical section type for a recognized heading.

    Exact aliases are preferred. A conservative uppercase heuristic is used
    only for headings that look strongly like section labels.
    """
    normalized = _normalize_heading(line)

    for canonical_type, aliases in SECTION_ALIASES.items():
        normalized_aliases = {
            _normalize_heading(alias)
            for alias in aliases
        }

        if normalized in normalized_aliases:
            return canonical_type

    # Conservative heading heuristic.
    stripped = line.strip()

    if (
        len(stripped) <= 50
        and stripped
        and not BULLET_PATTERN.match(stripped)
        and not any(character.isdigit() for character in stripped)
        and stripped.upper() == stripped
        and len(stripped.split()) <= 6
    ):
        upper_normalized = _normalize_heading(stripped)

        for canonical_type, aliases in SECTION_ALIASES.items():
            if upper_normalized in {
                _normalize_heading(alias)
                for alias in aliases
            }:
                return canonical_type

    return None

def _looks_like_custom_heading(line: str) -> bool:
    """
    Detect likely resume section headings that are not in SECTION_ALIASES.

    This intentionally uses conservative signals to avoid treating normal
    resume content such as company names, project titles, or bullet points
    as headings.
    """
    stripped = line.strip()

    if not stripped:
        return False

    if len(stripped) > 60:
        return False

    if BULLET_PATTERN.match(stripped):
        return False

    if EMAIL_PATTERN.search(stripped):
        return False

    if URL_PATTERN.search(stripped):
        return False

    if DATE_RANGE_PATTERN.search(stripped):
        return False

    if DEGREE_PATTERN.search(stripped):
        return False

    if ":" in stripped:
        return False

    words = stripped.split()

    if not 1 <= len(words) <= 6:
        return False

    # Strong resume-heading signal:
    # "Open Source Contributions"
    # "Personal Interests"
    # "Research Experience"
    title_case_words = sum(
        1
        for word in words
        if word and word[0].isupper()
    )

    if title_case_words < max(1, len(words) - 1):
        return False

    return True

def _extract_sections(
    lines: list[str],
) -> list[tuple[str, str, list[str]]]:
    """
    Split a resume into known sections while preserving their original
    document order.

    Important:
    A line inside a known section must not accidentally become a new
    section merely because it looks like a title. Entity-level parsing
    handles roles, institutions, project names, etc.
    """
    sections: list[tuple[str, str, list[str]]] = []

    current_type: str | None = None
    current_title: str | None = None
    current_content: list[str] = []

    def flush() -> None:
        nonlocal current_type
        nonlocal current_title
        nonlocal current_content

        if current_title is None:
            return

        sections.append(
            (
                current_type or "custom",
                current_title,
                current_content.copy(),
            )
        )

    for line in lines:
        heading = _heading_for(line)

        if heading is not None:
            flush()

            current_type = heading
            current_title = line.strip()
            current_content = []

            continue

        # Preserve unknown, title-like sections without allowing the first
        # institution/company/project line inside a known section to become
        # a false section heading. Requiring existing content is important
        # for cases such as:
        #
        #   Education
        #   Example University
        #   B.Tech Computer Science
        #   Open Source Contributions
        #
        # The first two lines belong to Education; the third starts the
        # custom section.
        if (
            current_title is not None
            and len(current_content) >= 2
            and _looks_like_custom_heading(line)
        ):
            flush()

            current_type = "custom"
            current_title = line.strip()
            current_content = []

            continue

        if current_title is None:
            continue

        current_content.append(line)

    flush()

    return sections


# ============================================================================
# Identity
# ============================================================================

def _extract_email(text: str) -> str | None:
    match = EMAIL_PATTERN.search(text)

    if match is None:
        return None

    return match.group(0)


def _looks_like_name(line: str) -> bool:
    if not 2 <= len(line) <= 60:
        return False

    if "@" in line:
        return False

    if "://" in line:
        return False

    if any(character.isdigit() for character in line):
        return False

    if ":" in line:
        return False

    words = line.split()

    return 1 <= len(words) <= 5


def _extract_name(lines: list[str]) -> str | None:
    """
    Look only near the beginning of the document.

    This prevents organization/project titles later in the resume from
    accidentally becoming the candidate's name.
    """
    for line in lines[:6]:
        if _heading_for(line) is not None:
            break

        cleaned = _clean_entry(line)

        if _looks_like_name(cleaned):
            return cleaned

    return None


# ============================================================================
# Summary
# ============================================================================

def _extract_summary(content: list[str]) -> str | None:
    if not content:
        return None

    cleaned = [
        _clean_entry(line)
        for line in content
        if _clean_entry(line)
    ]

    if not cleaned:
        return None

    return " ".join(cleaned)


# ============================================================================
# Skills
# ============================================================================

def _normalize_skill_label(label: str) -> str:
    label = label.strip().lower()
    label = re.sub(r"\s*/\s*", "/", label)
    label = re.sub(r"\s+", " ", label)

    return label


def _remove_skill_label(line: str) -> str:
    cleaned = _clean_entry(line)

    label, separator, values = cleaned.partition(":")

    if separator:
        normalized_label = _normalize_skill_label(label)

        if normalized_label in SKILL_SUBSECTION_LABELS:
            return values.strip()

    return cleaned


def _split_skills(content: list[str]) -> list[str]:
    skills: list[str] = []

    for line in content:
        values = _remove_skill_label(line)

        if not values:
            continue

        for skill in re.split(r"[,|•]", values):
            cleaned = _clean_entry(skill)

            if cleaned and cleaned not in skills:
                skills.append(cleaned)

    return skills


# ============================================================================
# Dates
# ============================================================================

def _extract_date_range(text: str) -> tuple[str | None, str | None]:
    match = DATE_RANGE_PATTERN.search(text)

    if match is None:
        return None, None

    return (
        match.group("start").strip(),
        match.group("end").strip(),
    )


def _extract_expected_graduation(text: str) -> str | None:
    match = EXPECTED_DATE_PATTERN.search(text)

    if match is None:
        return None

    return match.group("date").strip()


def _remove_date_range(text: str) -> str:
    return DATE_RANGE_PATTERN.sub("", text).strip()


# ============================================================================
# Education
# ============================================================================

def _looks_like_coursework(line: str) -> bool:
    normalized = line.lower()

    return (
        normalized.startswith("relevant coursework")
        or normalized.startswith("coursework")
        or normalized.startswith("relevant courses")
    )


def _extract_coursework(line: str) -> list[str]:
    _, separator, values = line.partition(":")

    if not separator:
        return []

    return [
        value.strip()
        for value in re.split(r"[,;|]", values)
        if value.strip()
    ]


def _extract_field_from_degree(degree_text: str) -> tuple[str | None, str | None]:
    """
    Convert:
        B.Tech, Computer Science & Engineering GPA: 8.97/10

    into:
        degree = B.Tech
        field = Computer Science & Engineering
    """
    cleaned = degree_text.strip()

    degree_match = DEGREE_PATTERN.search(cleaned)

    if degree_match is None:
        return None, None

    degree = degree_match.group(0).strip()

    remainder = cleaned[degree_match.end():]

    remainder = re.sub(
        r"^[,\s–—-]+",
        "",
        remainder,
    )

    remainder = GPA_PATTERN.sub("", remainder)
    remainder = re.sub(r"\s+", " ", remainder).strip(" ,|-")

    return degree, remainder or None


def _parse_education(content: list[str]) -> list[EducationEntry]:
    entries: list[EducationEntry] = []

    cleaned_lines = [
        _clean_entry(line)
        for line in content
        if _clean_entry(line)
    ]

    if not cleaned_lines:
        return entries

    current: EducationEntry | None = None
    raw_lines: list[str] = []

    for line in cleaned_lines:
        if _looks_like_coursework(line):
            coursework = _extract_coursework(line)

            if current is None:
                current = EducationEntry()

            current.coursework.extend(coursework)
            raw_lines.append(line)
            continue

        degree_match = DEGREE_PATTERN.search(line)

        if degree_match is not None:
            if current is None:
                current = EducationEntry()

            degree, field = _extract_field_from_degree(line)

            if degree:
                current.degree = degree

            if field:
                current.field_of_study = field

            gpa_match = GPA_PATTERN.search(line)

            if gpa_match:
                current.gpa = gpa_match.group("value").strip()

            raw_lines.append(line)
            continue

        expected_graduation = _extract_expected_graduation(line)

        if expected_graduation is not None:
            if current is None:
                current = EducationEntry()

            current.expected_graduation = expected_graduation

            institution_text = EXPECTED_DATE_PATTERN.sub("", line).strip()
            institution_text = institution_text.rstrip(",|-–— ")

            if institution_text:
                current.institution = institution_text

            raw_lines.append(line)
            continue

        # If there is no current education entity, treat the first line
        # as the institution.
        if current is None:
            current = EducationEntry()
            current.institution = line
            raw_lines.append(line)
            continue

        # A second institution after a completed education record.
        if (
            current.institution
            and current.degree
            and DEGREE_PATTERN.search(line) is None
            and not current.expected_graduation
            and not current.coursework
        ):
            current.raw_text = "\n".join(raw_lines)

            entries.append(current)

            current = EducationEntry(
                institution=line,
            )
            raw_lines = [line]
            continue

        if current.location is None and _looks_like_location(line):
            current.location = line
        else:
            raw_lines.append(line)

    if current is not None:
        current.raw_text = "\n".join(raw_lines)
        entries.append(current)

    return entries


# ============================================================================
# Experience
# ============================================================================

def _looks_like_role(line: str) -> bool:
    """
    Conservative role detection.

    We prefer short noun-like lines and avoid treating long bullet sentences
    as job titles.
    """
    if len(line) > 100:
        return False

    if BULLET_PATTERN.match(line):
        return False

    if SENTENCE_START_PATTERN.match(line):
        return False

    if DATE_RANGE_PATTERN.search(line):
        return False

    if line.endswith("."):
        return False

    return 1 <= len(line.split()) <= 8


def _looks_like_location(line: str) -> bool:
    """
    Detect likely location strings without inventing a location.

    This is deliberately conservative.
    """
    if len(line) > 80:
        return False

    normalized = line.lower()

    location_markers = (
        ", india",
        ", indore",
        ", delhi",
        ", mumbai",
        ", bengaluru",
        ", bangalore",
        ", pune",
        ", hyderabad",
        ", noida",
        ", gurugram",
        ", gurgaon",
        "remote",
        "hybrid",
        "on-site",
        "onsite",
    )

    return any(marker in normalized for marker in location_markers)


def _parse_experience_header(line: str) -> tuple[
    str | None,
    str | None,
    str | None,
    str | None,
]:
    """
    Parse a header such as:

        Student Developer Community (SDC), Medicaps University June 2026 – July 2026

    Returns:

        organization, location, start_date, end_date
    """
    start_date, end_date = _extract_date_range(line)

    without_dates = _remove_date_range(line)

    if not without_dates:
        return None, None, start_date, end_date

    organization = without_dates.strip(" ,|-–—")

    location: str | None = None

    # Explicit location after a pipe is strong evidence.
    if "|" in organization:
        organization, location = [
            part.strip()
            for part in organization.split("|", 1)
        ]

    return (
        organization or None,
        location,
        start_date,
        end_date,
    )


def _parse_experience(content: list[str]) -> list[ExperienceEntry]:
    entries: list[ExperienceEntry] = []

    lines = _merge_wrapped_bullets(content)

    if not lines:
        return entries

    current: ExperienceEntry | None = None
    raw_lines: list[str] = []

    for index, line in enumerate(lines):
        has_date = DATE_RANGE_PATTERN.search(line) is not None

        # A date-bearing line is the strongest experience-entry boundary.
        if has_date:
            if current is not None:
                current.raw_text = "\n".join(raw_lines)
                entries.append(current)

            (
                organization,
                location,
                start_date,
                end_date,
            ) = _parse_experience_header(line)

            current = ExperienceEntry(
                organization=organization,
                location=location,
                start_date=start_date,
                end_date=end_date,
            )

            raw_lines = [line]

            continue

        if current is None:
            # If no date exists, create a fallback entry.
            current = ExperienceEntry()
            raw_lines = []

        # The first short non-sentence line after the organization header
        # is usually the role.
        if current.role is None and _looks_like_role(line):
            current.role = line
            raw_lines.append(line)
            continue

        if current.location is None and _looks_like_location(line):
            current.location = line
            raw_lines.append(line)
            continue

        current.description.append(line)
        raw_lines.append(line)

    if current is not None:
        current.raw_text = "\n".join(raw_lines)
        entries.append(current)

    return entries


# ============================================================================
# Projects
# ============================================================================

def _extract_url(text: str) -> str | None:
    match = URL_PATTERN.search(text)

    if match is None:
        return None

    return match.group(0).rstrip(".,);]")


def _split_project_header(line: str) -> tuple[
    str | None,
    list[str],
    str | None,
]:
    """
    Parse common project header formats.

    Example:

        Plugs – LinkedIn Outreach Assistant | Flutter / FastAPI /
        Playwright / MongoDB / Ollama | github.com/Aaditya02123/Plugs
    """
    parts = [
        part.strip()
        for part in PROJECT_SPLIT_PATTERN.split(line)
        if part.strip()
    ]

    if len(parts) == 1:
        parts = [
            part.strip()
            for part in PROJECT_DASH_PATTERN.split(line)
            if part.strip()
        ]

    if not parts:
        return None, [], None

    title = parts[0]

    url = _extract_url(line)

    if url:
        title = title.strip()

    technologies: list[str] = []

    for part in parts[1:]:
        if URL_PATTERN.search(part):
            continue

        if "/" in part:
            technologies.extend(
                [
                    item.strip()
                    for item in part.split("/")
                    if item.strip()
                ]
            )

    # Remove URL-like text accidentally included in technology values.
    technologies = [
        technology
        for technology in technologies
        if not URL_PATTERN.search(technology)
    ]

    return (
        title or None,
        _unique(technologies),
        url,
    )


def _looks_like_project_header(line: str) -> bool:
    """Detect project title lines using strong metadata signals."""
    if _extract_url(line):
        return True

    if PROJECT_SPLIT_PATTERN.search(line):
        return True

    return False


def _split_embedded_project_header(line: str) -> list[str]:
    """
    Split a PDF line when a new project header is accidentally appended to
    the previous project's description.
    """
    matches = list(
        re.finditer(
            r"(?<=\.)\s+(?=[A-Z][^|]{2,100}\|)",
            line,
        )
    )

    if not matches:
        return [line]

    split_at = matches[-1].start()

    prefix = line[:split_at].strip()
    header = line[split_at:].strip()

    if not prefix or not header:
        return [line]

    return [prefix, header]


def _parse_projects(content: list[str]) -> list[ProjectEntry]:
    entries: list[ProjectEntry] = []

    # First reconstruct PDF-wrapped bullets while keeping non-bullet lines
    # such as project headers separate.
    merged_lines = _merge_wrapped_bullets(content)

    # Then repair the less common case where a PDF extractor joins the end
    # of one description and the next project's header onto one line.
    lines: list[str] = []
    for line in merged_lines:
        lines.extend(_split_embedded_project_header(line))

    current: ProjectEntry | None = None
    raw_lines: list[str] = []

    for line in lines:
        if not line:
            continue

        if _looks_like_project_header(line):
            if current is not None:
                current.raw_text = "\n".join(raw_lines)
                entries.append(current)

            title, technologies, url = _split_project_header(line)

            current = ProjectEntry(
                title=title,
                technologies=technologies,
                url=url,
            )

            raw_lines = [line]
            continue

        if current is None:
            current = ProjectEntry(title=line)
            raw_lines = [line]
            continue

        current.description.append(line)
        raw_lines.append(line)

    if current is not None:
        current.raw_text = "\n".join(raw_lines)
        entries.append(current)

    return entries


# ============================================================================
# Credentials
# ============================================================================

def _infer_credential_type(text: str) -> str:
    normalized = text.lower()

    # Participation is more specific than the generic "hackathon"
    # or "competition" classification.
    if "certificate of participation" in normalized:
        return "participation"

    if "participation" in normalized:
        return "participation"

    if "award" in normalized or "winner" in normalized:
        return "achievement"

    if "hackathon" in normalized or "competition" in normalized:
        return "competition"

    if "nptel" in normalized or "certification" in normalized:
        return "certification"

    return "other"


def _parse_credentials(
    content: list[str],
) -> list[CredentialEntry]:
    entries: list[CredentialEntry] = []

    for line in content:
        cleaned = _clean_entry(line)

        if not cleaned:
            continue

        credential_type = _infer_credential_type(cleaned)

        url = _extract_url(cleaned)

        title = cleaned

        if url:
            title = title.replace(url, "").strip(" |-")

        issuer: str | None = None

        if "NPTEL" in title.upper():
            parenthetical = re.search(r"\(([^)]+)\)", title)

            if parenthetical:
                issuer = parenthetical.group(1).strip()

        entries.append(
            CredentialEntry(
                title=title,
                issuer=issuer,
                credential_type=credential_type,
                url=url,
                raw_text=cleaned,
            )
        )

    return entries


# ============================================================================
# Generic / custom sections
# ============================================================================

def _generic_entries(
    content: list[str],
) -> list[ResumeEntry]:
    entries: list[ResumeEntry] = []

    for line in content:
        cleaned = _clean_entry(line)

        if cleaned:
            entries.append(
                ResumeEntry(
                    title=None,
                    content=[cleaned],
                    raw_text=cleaned,
                )
            )

    return entries


def _canonical_section(
    section_type: str,
    title: str,
    content: list[str],
) -> ResumeSection:
    return ResumeSection(
        title=title,
        canonical_type=section_type,  # type: ignore[arg-type]
        entries=_generic_entries(content),
        raw_content=content,
    )


# ============================================================================
# Utility
# ============================================================================

def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = value.strip().lower()

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        result.append(value.strip())

    return result


def _legacy_education(entries: list[EducationEntry]) -> list[str]:
    result: list[str] = []

    for entry in entries:
        parts = [
            entry.institution,
            entry.degree,
            entry.field_of_study,
            entry.expected_graduation,
            entry.gpa,
        ]

        combined = " | ".join(
            part.strip()
            for part in parts
            if part and part.strip()
        )

        if combined:
            result.append(combined)

        if entry.coursework:
            result.append(
                "Relevant Coursework: "
                + ", ".join(entry.coursework)
            )

    return result


def _legacy_experience(entries: list[ExperienceEntry]) -> list[str]:
    result: list[str] = []

    for entry in entries:
        metadata = " | ".join(
            part.strip()
            for part in [
                entry.organization,
                entry.role,
                entry.location,
                entry.start_date,
                entry.end_date,
            ]
            if part and part.strip()
        )

        if metadata:
            result.append(metadata)

        result.extend(entry.description)

    return result


def _legacy_projects(entries: list[ProjectEntry]) -> list[str]:
    result: list[str] = []

    for entry in entries:
        header_parts = [
            entry.title,
            (
                " / ".join(entry.technologies)
                if entry.technologies
                else None
            ),
            entry.url,
        ]

        header = " | ".join(
            part.strip()
            for part in header_parts
            if part and part.strip()
        )

        if header:
            result.append(header)

        result.extend(entry.description)

    return result


def _legacy_credentials(
    entries: list[CredentialEntry],
) -> list[str]:
    return [entry.title for entry in entries]


# ============================================================================
# Main parser
# ============================================================================

def parse_resume_text(text: str) -> StructuredResume:
    """
    Parse a resume into CareerLens's canonical structured representation.

    The parser is section-aware and entity-aware.

    Important:
    - It does not assume every resume has the same sections.
    - Unknown sections are preserved.
    - Important sections receive typed entities.
    - Raw evidence is retained.
    - Missing information remains None rather than being invented.
    """
    lines = _normalize_lines(text)

    section_blocks = _extract_sections(lines)

    summary: str | None = None

    education_entries: list[EducationEntry] = []
    experience_entries: list[ExperienceEntry] = []
    project_entries: list[ProjectEntry] = []
    credential_entries: list[CredentialEntry] = []

    skills: list[str] = []
    sections: list[ResumeSection] = []

    for section_type, title, content in section_blocks:
        if section_type == "summary":
            summary = _extract_summary(content)

        elif section_type == "skills":
            skills = _split_skills(content)

        elif section_type == "education":
            education_entries = _parse_education(content)

        elif section_type == "experience":
            experience_entries = _parse_experience(content)

        elif section_type == "projects":
            project_entries = _parse_projects(content)

        elif section_type == "certifications":
            credential_entries = _parse_credentials(content)

        else:
            sections.append(
                _canonical_section(
                    section_type,
                    title,
                    content,
                )
            )

    # Add the specialized sections too, so the complete resume section
    # order is preserved for the frontend.
    for section_type, title, content in section_blocks:
        if section_type == "summary":
            sections.append(
                _canonical_section(
                    "summary",
                    title,
                    content,
                )
            )

        elif section_type == "skills":
            sections.append(
                _canonical_section(
                    "skills",
                    title,
                    content,
                )
            )

        elif section_type == "education":
            sections.append(
                ResumeSection(
                    title=title,
                    canonical_type="education",
                    entries=[
                        ResumeEntry(
                            title=entry.institution,
                            content=[
                                value
                                for value in [
                                    entry.degree,
                                    entry.field_of_study,
                                    entry.location,
                                    entry.expected_graduation,
                                    entry.gpa,
                                ]
                                if value
                            ]
                            + (
                                ["Relevant Coursework: "
                                 + ", ".join(entry.coursework)]
                                if entry.coursework
                                else []
                            ),
                            raw_text=entry.raw_text,
                        )
                        for entry in education_entries
                    ],
                    raw_content=content,
                )
            )

        elif section_type == "experience":
            sections.append(
                ResumeSection(
                    title=title,
                    canonical_type="experience",
                    entries=[
                        ResumeEntry(
                            title=entry.role or entry.organization,
                            content=(
                                [
                                    value
                                    for value in [
                                        entry.organization,
                                        entry.location,
                                        (
                                            f"{entry.start_date} – "
                                            f"{entry.end_date}"
                                            if entry.start_date
                                            and entry.end_date
                                            else entry.start_date
                                            or entry.end_date
                                        ),
                                    ]
                                    if value
                                ]
                                + entry.description
                            ),
                            raw_text=entry.raw_text,
                        )
                        for entry in experience_entries
                    ],
                    raw_content=content,
                )
            )

        elif section_type == "projects":
            sections.append(
                ResumeSection(
                    title=title,
                    canonical_type="projects",
                    entries=[
                        ResumeEntry(
                            title=entry.title,
                            content=(
                                (
                                    ["Technologies: "
                                     + ", ".join(entry.technologies)]
                                    if entry.technologies
                                    else []
                                )
                                + (
                                    ["URL: " + entry.url]
                                    if entry.url
                                    else []
                                )
                                + entry.description
                            ),
                            raw_text=entry.raw_text,
                        )
                        for entry in project_entries
                    ],
                    raw_content=content,
                )
            )

        elif section_type == "certifications":
            sections.append(
                ResumeSection(
                    title=title,
                    canonical_type="certifications",
                    entries=[
                        ResumeEntry(
                            title=entry.title,
                            content=[
                                value
                                for value in [
                                    entry.issuer,
                                    entry.credential_type,
                                    entry.date,
                                    entry.url,
                                ]
                                if value
                            ],
                            raw_text=entry.raw_text,
                        )
                        for entry in credential_entries
                    ],
                    raw_content=content,
                )
            )

    return StructuredResume(
        name=_extract_name(lines),
        email=_extract_email(text),
        summary=summary,
        skills=skills,
        education=_legacy_education(education_entries),
        experience=_legacy_experience(experience_entries),
        projects=_legacy_projects(project_entries),
        certifications=_legacy_credentials(credential_entries),
        education_entries=education_entries,
        experience_entries=experience_entries,
        project_entries=project_entries,
        credential_entries=credential_entries,
        sections=sections,
    )