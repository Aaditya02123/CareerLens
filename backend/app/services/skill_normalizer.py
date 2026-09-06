from collections.abc import Iterable


CANONICAL_SKILLS = (
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


SKILL_NORMALIZATION_MAP = {
    skill.lower(): skill
    for skill in CANONICAL_SKILLS
}

SKILL_NORMALIZATION_MAP.update(
    {
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "reactjs": "React",
        "react.js": "React",
        "nodejs": "Node.js",
        "node.js": "Node.js",
        "ml": "Machine Learning",
        "machine learning": "Machine Learning",
        "dl": "Deep Learning",
        "deep learning": "Deep Learning",
        "nlp": "Natural Language Processing",
        "natural language processing": "Natural Language Processing",
        "oop": "Object-Oriented Programming",
        "object oriented programming": "Object-Oriented Programming",
        "object-oriented programming": "Object-Oriented Programming",
    }
)


def normalize_skills(skills: list[str]) -> list[str]:
    """Normalize known skills and remove duplicates in first-seen order."""
    normalized_skills = []
    seen_skills = set()

    for skill in skills:
        cleaned_skill = skill.strip()
        lookup_key = cleaned_skill.lower()
        canonical_skill = SKILL_NORMALIZATION_MAP.get(lookup_key,cleaned_skill,)
        deduplication_key = canonical_skill.strip().lower()

        if deduplication_key in seen_skills:
            continue

        seen_skills.add(deduplication_key)
        normalized_skills.append(canonical_skill)

    return normalized_skills