import re

from app.models.skills import SkillExtractionResult


SKILL_VOCABULARY = (
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "C",
    "C++",
    "C#",
    "React",
    "Angular",
    "Vue.js",
    "FastAPI",
    "Django",
    "Flask",
    "Node.js",
    "Express.js",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "Google Cloud",
    "Machine Learning",
    "Deep Learning",
    "Natural Language Processing",
    "Computer Vision",
    "TensorFlow",
    "PyTorch",
    "Git",
    "GitHub",
)


def _compile_skill_pattern(skill: str) -> re.Pattern[str]:
    """Create a case-insensitive pattern with safe skill boundaries."""
    escaped_skill = re.escape(skill)

    return re.compile(
        rf"(?<![A-Za-z0-9+#]){escaped_skill}(?![A-Za-z0-9+#])",
        re.IGNORECASE,
    )


SKILL_PATTERNS = {
    skill: _compile_skill_pattern(skill)
    for skill in SKILL_VOCABULARY
}


def _normalize_text(text: str) -> str:
    """Normalize whitespace so skills can span extracted text line breaks."""
    return re.sub(r"\s+", " ", text).strip()


def extract_skills(text: str) -> SkillExtractionResult:
    """Extract canonical skills from the entire resume text."""
    normalized_text = _normalize_text(text)

    matched_skills = [
        skill
        for skill in SKILL_VOCABULARY
        if SKILL_PATTERNS[skill].search(normalized_text)
    ]

    return SkillExtractionResult(skills=matched_skills)