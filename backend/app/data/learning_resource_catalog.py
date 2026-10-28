from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse


LearningResourceType = Literal[
    "official_docs",
    "tutorial",
    "practice",
    "course",
]

LearningResourceLevel = Literal[
    "beginner",
    "intermediate",
    "advanced",
]


@dataclass(frozen=True)
class LearningResource:
    """An immutable curated resource for one normalized skill."""

    id: str
    skill: str
    title: str
    url: str
    provider: str
    resource_type: LearningResourceType
    level: LearningResourceLevel


def normalize_skill_key(skill: str) -> str:
    """Normalize a skill for deterministic case-insensitive lookup."""
    return " ".join(skill.casefold().strip().split())


LEARNING_RESOURCE_CATALOG: dict[
    str,
    tuple[LearningResource, ...],
] = {
    "python": (
        LearningResource(
            id="python-official-tutorial",
            skill="python",
            title="The Python Tutorial",
            url="https://docs.python.org/3/tutorial/",
            provider="Python Software Foundation",
            resource_type="official_docs",
            level="beginner",
        ),
        LearningResource(
            id="python-exercism",
            skill="python",
            title="Python Track",
            url="https://exercism.org/tracks/python",
            provider="Exercism",
            resource_type="practice",
            level="beginner",
        ),
    ),
    "sql": (
        LearningResource(
            id="sqlbolt-lessons",
            skill="sql",
            title="SQLBolt Interactive Lessons",
            url="https://sqlbolt.com/",
            provider="SQLBolt",
            resource_type="tutorial",
            level="beginner",
        ),
        LearningResource(
            id="sqltutorial-reference",
            skill="sql",
            title="SQL Tutorial",
            url="https://www.sqltutorial.org/",
            provider="SQLTutorial.org",
            resource_type="tutorial",
            level="beginner",
        ),
    ),
    "fastapi": (
        LearningResource(
            id="fastapi-official-tutorial",
            skill="fastapi",
            title="FastAPI Tutorial",
            url="https://fastapi.tiangolo.com/tutorial/",
            provider="FastAPI",
            resource_type="official_docs",
            level="beginner",
        ),
        LearningResource(
            id="fastapi-advanced-user-guide",
            skill="fastapi",
            title="FastAPI Advanced User Guide",
            url="https://fastapi.tiangolo.com/advanced/",
            provider="FastAPI",
            resource_type="official_docs",
            level="intermediate",
        ),
    ),
    "postgresql": (
        LearningResource(
            id="postgresql-official-tutorial",
            skill="postgresql",
            title="PostgreSQL Tutorial",
            url="https://www.postgresql.org/docs/current/tutorial.html",
            provider="PostgreSQL",
            resource_type="official_docs",
            level="beginner",
        ),
        LearningResource(
            id="postgresql-exercises",
            skill="postgresql",
            title="PostgreSQL Exercises",
            url="https://pgexercises.com/",
            provider="PostgreSQL Exercises",
            resource_type="practice",
            level="beginner",
        ),
    ),
    "git": (
        LearningResource(
            id="git-official-book",
            skill="git",
            title="Pro Git",
            url="https://git-scm.com/book/en/v2",
            provider="Git",
            resource_type="official_docs",
            level="beginner",
        ),
        LearningResource(
            id="github-skills-introduction",
            skill="git",
            title="Introduction to GitHub",
            url="https://skills.github.com/",
            provider="GitHub Skills",
            resource_type="tutorial",
            level="beginner",
        ),
    ),
    "docker": (
        LearningResource(
            id="docker-get-started",
            skill="docker",
            title="Get Started with Docker",
            url="https://docs.docker.com/get-started/",
            provider="Docker",
            resource_type="official_docs",
            level="beginner",
        ),
        LearningResource(
            id="docker-play-with-docker",
            skill="docker",
            title="Play with Docker Classroom",
            url="https://training.play-with-docker.com/",
            provider="Docker",
            resource_type="practice",
            level="beginner",
        ),
    ),
    "react": (
        LearningResource(
            id="react-official-learn",
            skill="react",
            title="Learn React",
            url="https://react.dev/learn",
            provider="React",
            resource_type="official_docs",
            level="beginner",
        ),
        LearningResource(
            id="react-new-projects",
            skill="react",
            title="Start a New React Project",
            url="https://react.dev/learn/start-a-new-react-project",
            provider="React",
            resource_type="official_docs",
            level="beginner",
        ),
    ),
    "machine learning": (
        LearningResource(
            id="google-machine-learning-crash-course",
            skill="machine learning",
            title="Machine Learning Crash Course",
            url="https://developers.google.com/machine-learning/crash-course",
            provider="Google",
            resource_type="course",
            level="beginner",
        ),
        LearningResource(
            id="scikit-learn-user-guide",
            skill="machine learning",
            title="Scikit-learn User Guide",
            url="https://scikit-learn.org/stable/user_guide.html",
            provider="Scikit-learn",
            resource_type="official_docs",
            level="intermediate",
        ),
    ),
    "rest apis": (
        LearningResource(
            id="mdn-http-overview",
            skill="rest apis",
            title="HTTP Overview",
            url="https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview",
            provider="MDN Web Docs",
            resource_type="official_docs",
            level="beginner",
        ),
        LearningResource(
            id="postman-api-fundamentals",
            skill="rest apis",
            title="API Fundamentals",
            url="https://learning.postman.com/docs/getting-started/introduction/",
            provider="Postman",
            resource_type="tutorial",
            level="beginner",
        ),
    ),
}


_ALLOWED_RESOURCE_TYPES = {
    "official_docs",
    "tutorial",
    "practice",
    "course",
}

_ALLOWED_RESOURCE_LEVELS = {
    "beginner",
    "intermediate",
    "advanced",
}


class CatalogValidationError(ValueError):
    """Raised when the curated learning-resource catalog is invalid."""


def validate_learning_resource_catalog(
    catalog: Mapping[
        str,
        Sequence[LearningResource],
    ] = LEARNING_RESOURCE_CATALOG,
) -> None:
    """Validate catalog structure without making network requests."""
    seen_resource_ids: set[str] = set()

    for catalog_key, resources in catalog.items():
        if not isinstance(catalog_key, str):
            raise CatalogValidationError(
                "Catalog keys must be strings."
            )

        if not catalog_key.strip():
            raise CatalogValidationError(
                "Catalog keys must not be empty."
            )

        if normalize_skill_key(catalog_key) != catalog_key:
            raise CatalogValidationError(
                f"Catalog key is not normalized: {catalog_key!r}"
            )

        if (
            isinstance(resources, (str, bytes))
            or not isinstance(resources, Sequence)
        ):
            raise CatalogValidationError(
                f"Resources for {catalog_key!r} must be a "
                "sequence of LearningResource objects, not a "
                "string or bytes value."
            )

        for index, resource in enumerate(resources):
            if not isinstance(resource, LearningResource):
                raise CatalogValidationError(
                    f"Resource at {catalog_key!r}[{index}] must "
                    "be a LearningResource instance."
                )

            required_fields = {
                "id": resource.id,
                "skill": resource.skill,
                "title": resource.title,
                "url": resource.url,
                "provider": resource.provider,
                "resource_type": resource.resource_type,
                "level": resource.level,
            }

            for field_name, value in required_fields.items():
                if not isinstance(value, str) or not value.strip():
                    raise CatalogValidationError(
                        f"{field_name} must be a non-empty string "
                        f"for resource at {catalog_key!r}[{index}]."
                    )

            if resource.id in seen_resource_ids:
                raise CatalogValidationError(
                    f"Duplicate resource ID: {resource.id!r}"
                )

            seen_resource_ids.add(resource.id)

            if (
                normalize_skill_key(resource.skill)
                != catalog_key
            ):
                raise CatalogValidationError(
                    f"Resource skill {resource.skill!r} does not "
                    f"match catalog key {catalog_key!r}."
                )

            if resource.resource_type not in (
                _ALLOWED_RESOURCE_TYPES
            ):
                raise CatalogValidationError(
                    f"Unsupported resource type "
                    f"{resource.resource_type!r} at "
                    f"{catalog_key!r}[{index}]."
                )

            if resource.level not in _ALLOWED_RESOURCE_LEVELS:
                raise CatalogValidationError(
                    f"Unsupported resource level "
                    f"{resource.level!r} at "
                    f"{catalog_key!r}[{index}]."
                )

            try:
                parsed_url = urlparse(resource.url)
                hostname = parsed_url.hostname
                parsed_url.port
            except ValueError as error:
                raise CatalogValidationError(
                    f"Invalid URL for resource "
                    f"{resource.id!r}: {resource.url!r}"
                ) from error

            if parsed_url.scheme not in {"http", "https"}:
                raise CatalogValidationError(
                    f"URL for resource {resource.id!r} must use "
                    f"http or https: {resource.url!r}"
                )

            authority = parsed_url.netloc.rsplit("@", 1)[-1]

            if authority.endswith(":"):
                raise CatalogValidationError(
                    f"URL for resource {resource.id!r} has "
                    f"an empty port: {resource.url!r}"
                )

            if not parsed_url.netloc or not hostname:
                raise CatalogValidationError(
                    f"URL for resource {resource.id!r} must include "
                    f"a valid hostname: {resource.url!r}"
                )


def get_learning_resources(
    skill: str,
) -> tuple[LearningResource, ...]:
    """Return resources for a normalized skill or an empty tuple."""
    return LEARNING_RESOURCE_CATALOG.get(
        normalize_skill_key(skill),
        (),
    )