from collections.abc import Mapping

from dataclasses import dataclass

from app.data.learning_resource_catalog import normalize_skill_key


@dataclass(frozen=True)
class LearningEffortEstimate:
    """Curated effort ranges for partial and missing skill gaps."""

    partial_min_hours: int
    partial_max_hours: int
    missing_min_hours: int
    missing_max_hours: int


LEARNING_EFFORT_CATALOG: dict[str, LearningEffortEstimate] = {
    "python": LearningEffortEstimate(
        partial_min_hours=4,
        partial_max_hours=8,
        missing_min_hours=12,
        missing_max_hours=20,
    ),
    "sql": LearningEffortEstimate(
        partial_min_hours=3,
        partial_max_hours=6,
        missing_min_hours=10,
        missing_max_hours=16,
    ),
    "fastapi": LearningEffortEstimate(
        partial_min_hours=4,
        partial_max_hours=8,
        missing_min_hours=12,
        missing_max_hours=20,
    ),
    "postgresql": LearningEffortEstimate(
        partial_min_hours=3,
        partial_max_hours=6,
        missing_min_hours=8,
        missing_max_hours=14,
    ),
    "git": LearningEffortEstimate(
        partial_min_hours=1,
        partial_max_hours=3,
        missing_min_hours=4,
        missing_max_hours=8,
    ),
    "docker": LearningEffortEstimate(
        partial_min_hours=3,
        partial_max_hours=6,
        missing_min_hours=8,
        missing_max_hours=14,
    ),
    "react": LearningEffortEstimate(
        partial_min_hours=4,
        partial_max_hours=8,
        missing_min_hours=12,
        missing_max_hours=20,
    ),
    "machine learning": LearningEffortEstimate(
        partial_min_hours=8,
        partial_max_hours=14,
        missing_min_hours=25,
        missing_max_hours=40,
    ),
    "rest apis": LearningEffortEstimate(
        partial_min_hours=3,
        partial_max_hours=6,
        missing_min_hours=8,
        missing_max_hours=14,
    ),
}


class LearningEffortCatalogValidationError(ValueError):
    """Raised when the effort catalog contains invalid data."""


def validate_learning_effort_catalog(
    catalog: Mapping[str, LearningEffortEstimate] = (
        LEARNING_EFFORT_CATALOG
    ),
) -> None:
    """Validate catalog keys, ranges, and partial/missing ordering."""
    for catalog_key, estimate in catalog.items():
        if not isinstance(catalog_key, str):
            raise LearningEffortCatalogValidationError(
                "Catalog keys must be strings."
            )

        if not catalog_key.strip():
            raise LearningEffortCatalogValidationError(
                "Catalog keys must not be empty."
            )

        if normalize_skill_key(catalog_key) != catalog_key:
            raise LearningEffortCatalogValidationError(
                f"Catalog key is not normalized: {catalog_key!r}"
            )

        if not isinstance(estimate, LearningEffortEstimate):
            raise LearningEffortCatalogValidationError(
                f"Catalog value for {catalog_key!r} must be a "
                "LearningEffortEstimate."
            )

        values = {
            "partial_min_hours": estimate.partial_min_hours,
            "partial_max_hours": estimate.partial_max_hours,
            "missing_min_hours": estimate.missing_min_hours,
            "missing_max_hours": estimate.missing_max_hours,
        }

        for field_name, value in values.items():
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value <= 0
            ):
                raise LearningEffortCatalogValidationError(
                    f"{field_name} for {catalog_key!r} must be "
                    "a positive integer."
                )

        if estimate.partial_min_hours > estimate.partial_max_hours:
            raise LearningEffortCatalogValidationError(
                f"Partial minimum hours exceed the maximum for "
                f"{catalog_key!r}."
            )

        if estimate.missing_min_hours > estimate.missing_max_hours:
            raise LearningEffortCatalogValidationError(
                f"Missing minimum hours exceed the maximum for "
                f"{catalog_key!r}."
            )

        if estimate.partial_max_hours >= estimate.missing_min_hours:
            raise LearningEffortCatalogValidationError(
                f"Partial effort must be lower than missing effort "
                f"for {catalog_key!r}."
            )


def get_learning_effort_estimate(
    skill: str,
) -> LearningEffortEstimate | None:
    """Return the normalized skill's estimate, if one is cataloged."""
    return LEARNING_EFFORT_CATALOG.get(
        normalize_skill_key(skill),
    )