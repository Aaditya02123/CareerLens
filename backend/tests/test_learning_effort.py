import pytest
from pydantic import ValidationError

from app.data.learning_effort_catalog import (
    LEARNING_EFFORT_CATALOG,
    LearningEffortEstimate,
    LearningEffortCatalogValidationError,
    validate_learning_effort_catalog,
)
from app.models.learning_effort import LearningEffortResponse
from app.services.learning_effort_service import (
    estimate_learning_effort,
)


@pytest.mark.parametrize(
    ("skill", "partial_range", "missing_range"),
    [
        ("Python", (4, 8), (12, 20)),
        ("SQL", (3, 6), (10, 16)),
        ("FastAPI", (4, 8), (12, 20)),
        ("PostgreSQL", (3, 6), (8, 14)),
        ("Git", (1, 3), (4, 8)),
        ("Docker", (3, 6), (8, 14)),
        ("React", (4, 8), (12, 20)),
        ("Machine Learning", (8, 14), (25, 40)),
        ("REST APIs", (3, 6), (8, 14)),
    ],
)
def test_known_skill_returns_expected_effort_ranges(
    skill,
    partial_range,
    missing_range,
):
    partial = estimate_learning_effort(skill, "partial")
    missing = estimate_learning_effort(skill, "missing")

    assert partial.available is True
    assert (
        partial.minimum_hours,
        partial.maximum_hours,
    ) == partial_range

    assert missing.available is True
    assert (
        missing.minimum_hours,
        missing.maximum_hours,
    ) == missing_range


def test_partial_effort_is_lower_than_missing_effort():
    partial = estimate_learning_effort("Python", "partial")
    missing = estimate_learning_effort("Python", "missing")

    assert partial.maximum_hours < missing.minimum_hours


def test_skill_lookup_is_case_and_whitespace_insensitive():
    normalized = estimate_learning_effort(
        "machine learning",
        "missing",
    )
    varied = estimate_learning_effort(
        "  MaChInE   LeArNiNg  ",
        "missing",
    )

    assert varied == normalized


def test_unknown_skill_returns_unavailable_estimate():
    result = estimate_learning_effort(
        "Kubernetes",
        "missing",
    )

    assert result.skill == "kubernetes"
    assert result.gap_status == "missing"
    assert result.available is False
    assert result.minimum_hours is None
    assert result.maximum_hours is None


@pytest.mark.parametrize(
    "gap_status",
    ["matched", "partial ", "", None],
)
def test_invalid_gap_status_is_rejected(gap_status):
    with pytest.raises(ValueError):
        estimate_learning_effort("Python", gap_status)


def test_empty_skill_is_rejected():
    with pytest.raises(ValueError):
        estimate_learning_effort("   ", "partial")


def test_estimate_results_are_deterministic():
    first = estimate_learning_effort("React", "missing")
    second = estimate_learning_effort("React", "missing")

    assert first == second


def test_available_response_requires_both_hour_values():
    with pytest.raises(ValidationError):
        LearningEffortResponse(
            skill="python",
            gap_status="partial",
            minimum_hours=4,
            maximum_hours=None,
            available=True,
        )


def test_unavailable_response_rejects_hour_values():
    with pytest.raises(ValidationError):
        LearningEffortResponse(
            skill="unknown",
            gap_status="missing",
            minimum_hours=1,
            maximum_hours=None,
            available=False,
        )


def test_response_rejects_reversed_hour_range():
    with pytest.raises(ValidationError):
        LearningEffortResponse(
            skill="python",
            gap_status="partial",
            minimum_hours=8,
            maximum_hours=4,
            available=True,
        )


def test_effort_catalog_is_valid():
    validate_learning_effort_catalog()


def test_effort_catalog_rejects_unnormalized_key():
    catalog = dict(LEARNING_EFFORT_CATALOG)
    catalog[" Python "] = catalog.pop("python")

    with pytest.raises(
        LearningEffortCatalogValidationError,
        match="not normalized",
    ):
        validate_learning_effort_catalog(catalog)


def test_effort_catalog_rejects_invalid_range():
    catalog = {
        "python": LearningEffortEstimate(
            partial_min_hours=8,
            partial_max_hours=4,
            missing_min_hours=12,
            missing_max_hours=20,
        ),
    }

    with pytest.raises(
        LearningEffortCatalogValidationError,
        match="Partial minimum hours",
    ):
        validate_learning_effort_catalog(catalog)