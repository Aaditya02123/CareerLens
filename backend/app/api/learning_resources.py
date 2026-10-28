from fastapi import APIRouter

from app.data.learning_resource_catalog import normalize_skill_key
from app.models.learning_resource import (
    LearningResourceLookupResponse,
    LearningResourceResponse,
)
from app.services.learning_resource_service import (
    get_learning_resources_for_skill,
)


router = APIRouter()


@router.get(
    "/learning-resources/{skill}",
    response_model=LearningResourceLookupResponse,
)
def get_learning_resources(
    skill: str,
) -> LearningResourceLookupResponse:
    """Return curated learning resources for a requested skill."""
    normalized_skill = normalize_skill_key(skill)
    resources = get_learning_resources_for_skill(skill)

    return LearningResourceLookupResponse(
        skill=normalized_skill,
        total_resources=len(resources),
        resources=[
            LearningResourceResponse.model_validate(resource)
            for resource in resources
        ],
    )