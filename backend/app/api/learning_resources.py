from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.data.learning_resource_catalog import normalize_skill_key
from app.models.learning_resource import (
    LearningResourceLookupResponse,
    LearningResourceResponse,
)
from app.services.learning_resource_service import (
    get_learning_resources_for_skill,
    get_learning_resources_for_user,
)
from app.services.learning_preferences_service import (
    LearningPreferencesUserNotFoundError,
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


@router.get(
    "/users/{user_id}/learning-resources/{skill}",
    response_model=LearningResourceLookupResponse,
)
def get_personalized_learning_resources(
    user_id: int,
    skill: str,
    db: Session = Depends(get_db),
) -> LearningResourceLookupResponse:
    """Return curated resources ordered for a user's preferences."""
    try:
        normalized_skill = normalize_skill_key(skill)
        resources = get_learning_resources_for_user(
            user_id=user_id,
            skill=skill,
            session=db,
        )
    except LearningPreferencesUserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The specified user was not found.",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Learning resources could not be loaded.",
        ) from error

    return LearningResourceLookupResponse(
        skill=normalized_skill,
        total_resources=len(resources),
        resources=[
            LearningResourceResponse.model_validate(resource)
            for resource in resources
        ],
    )
