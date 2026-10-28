from dataclasses import replace
from urllib.parse import urlparse

import pytest

from app.data.learning_resource_catalog import (
    LEARNING_RESOURCE_CATALOG,
    CatalogValidationError,
    LearningResource,
    get_learning_resources,
    normalize_skill_key,
    validate_learning_resource_catalog,
)


def catalog_with_replacement(
    catalog_key: str,
    replacement: LearningResource,
    *,
    replacement_key: str | None = None,
):
    catalog = dict(LEARNING_RESOURCE_CATALOG)
    key = (
        replacement_key
        if replacement_key is not None
        else catalog_key
    )
    catalog[key] = (replacement,)
    return catalog


def test_learning_resource_catalog_is_valid():
    validate_learning_resource_catalog()


def test_existing_catalog_entries_are_complete_and_well_formed():
    resource_ids = set()

    for catalog_key, resources in (
        LEARNING_RESOURCE_CATALOG.items()
    ):
        assert normalize_skill_key(catalog_key) == catalog_key

        for resource in resources:
            assert isinstance(resource, LearningResource)
            assert resource.id
            assert resource.id not in resource_ids
            resource_ids.add(resource.id)

            assert resource.skill
            assert (
                normalize_skill_key(resource.skill)
                == catalog_key
            )
            assert resource.title
            assert resource.provider
            assert resource.resource_type
            assert resource.level

            parsed_url = urlparse(resource.url)
            assert parsed_url.scheme in {"http", "https"}
            assert parsed_url.hostname
            parsed_url.port


def test_duplicate_resource_ids_are_rejected():
    python_resources = LEARNING_RESOURCE_CATALOG["python"]

    duplicate = replace(
        python_resources[1],
        id=python_resources[0].id,
    )

    catalog = {
        "python": (
            python_resources[0],
            duplicate,
        ),
    }

    with pytest.raises(
        CatalogValidationError,
        match="Duplicate resource ID",
    ):
        validate_learning_resource_catalog(catalog)


def test_unnormalized_catalog_keys_are_rejected():
    resource = LEARNING_RESOURCE_CATALOG["python"][0]

    catalog = catalog_with_replacement(
        "python",
        resource,
        replacement_key=" Python ",
    )

    with pytest.raises(
        CatalogValidationError,
        match="not normalized",
    ):
        validate_learning_resource_catalog(catalog)


def test_empty_catalog_key_is_preserved_and_rejected():
    resource = LEARNING_RESOURCE_CATALOG["python"][0]

    catalog = catalog_with_replacement(
        "python",
        resource,
        replacement_key="",
    )

    with pytest.raises(
        CatalogValidationError,
        match="must not be empty",
    ):
        validate_learning_resource_catalog(catalog)


def test_resource_skill_mismatch_is_rejected():
    resource = replace(
        LEARNING_RESOURCE_CATALOG["python"][0],
        skill="sql",
    )

    catalog = catalog_with_replacement(
        "python",
        resource,
    )

    with pytest.raises(
        CatalogValidationError,
        match="does not match catalog key",
    ):
        validate_learning_resource_catalog(catalog)


def test_invalid_resource_type_is_rejected():
    resource = replace(
        LEARNING_RESOURCE_CATALOG["python"][0],
        resource_type="video",
    )

    catalog = catalog_with_replacement(
        "python",
        resource,
    )

    with pytest.raises(
        CatalogValidationError,
        match="Unsupported resource type",
    ):
        validate_learning_resource_catalog(catalog)


def test_invalid_resource_level_is_rejected():
    resource = replace(
        LEARNING_RESOURCE_CATALOG["python"][0],
        level="expert",
    )

    catalog = catalog_with_replacement(
        "python",
        resource,
    )

    with pytest.raises(
        CatalogValidationError,
        match="Unsupported resource level",
    ):
        validate_learning_resource_catalog(catalog)


@pytest.mark.parametrize(
    "url",
    [
        "not-a-url",
        "ftp://example.com/resource",
        "https://example.com:invalid/resource",
        "https://example.com:99999/resource",
        "https://example.com:/resource",
        "https://[invalid/resource",
    ],
)
def test_malformed_urls_are_rejected(url):
    resource = replace(
        LEARNING_RESOURCE_CATALOG["python"][0],
        url=url,
    )

    catalog = catalog_with_replacement(
        "python",
        resource,
    )

    with pytest.raises(
        CatalogValidationError,
        match="URL",
    ):
        validate_learning_resource_catalog(catalog)


@pytest.mark.parametrize(
    "invalid_entry",
    [
        object(),
        "not a resource",
        b"not a resource",
    ],
)
def test_invalid_resource_objects_are_rejected(invalid_entry):
    catalog = {
        "python": (invalid_entry,),
    }

    with pytest.raises(
        CatalogValidationError,
        match="LearningResource instance",
    ):
        validate_learning_resource_catalog(catalog)


@pytest.mark.parametrize(
    "invalid_collection",
    [
        "not a resource sequence",
        b"not a resource sequence",
        object(),
    ],
)
def test_invalid_resource_collections_are_rejected(
    invalid_collection,
):
    catalog = {
        "python": invalid_collection,
    }

    with pytest.raises(
        CatalogValidationError,
        match="sequence of LearningResource",
    ):
        validate_learning_resource_catalog(catalog)


def test_learning_resource_lookup_is_case_and_whitespace_insensitive():
    resources = get_learning_resources("  PyThOn ")

    assert resources
    assert all(resource.skill == "python" for resource in resources)


def test_unknown_learning_resource_lookup_returns_empty_tuple():
    assert get_learning_resources("unknown skill") == ()