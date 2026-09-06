from app.models.skills import (
    CategorizedSkillResult,
    Skill,
    SkillCategory,
)


SKILL_CATEGORIES = {
    SkillCategory.PROGRAMMING_LANGUAGE: {
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "C",
        "C++",
        "C#",
    },
    SkillCategory.FRAMEWORK_LIBRARY: {
        "React",
        "Angular",
        "Vue.js",
        "FastAPI",
        "Django",
        "Flask",
        "Node.js",
        "Express.js",
    },
    SkillCategory.DATABASE: {
        "PostgreSQL",
        "MySQL",
        "MongoDB",
        "Redis",
    },
    SkillCategory.CLOUD: {
        "AWS",
        "Azure",
        "Google Cloud",
    },
    SkillCategory.DEVOPS_INFRASTRUCTURE: {
        "Docker",
        "Kubernetes",
    },
    SkillCategory.AI_ML: {
        "Machine Learning",
        "Deep Learning",
        "Natural Language Processing",
        "Computer Vision",
        "TensorFlow",
        "PyTorch",
    },
    SkillCategory.TOOLS: {
        "Git",
        "GitHub",
    },
    SkillCategory.CORE_CS: set(),
}


def _category_for_skill(skill_name: str) -> SkillCategory:
    """Return the category assigned to a canonical skill name."""
    for category, skills in SKILL_CATEGORIES.items():
        if skill_name in skills:
            return category

    return SkillCategory.OTHER


def categorize_skills(skills: list[str]) -> CategorizedSkillResult:
    """Assign one deterministic category to each skill in input order."""
    categorized_skills = [
        Skill(
            name=skill_name,
            category=_category_for_skill(skill_name),
        )
        for skill_name in skills
    ]

    return CategorizedSkillResult(skills=categorized_skills)