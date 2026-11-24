from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_current_user_id
from app.models.learning_preferences import (
    LearningPreferencesResponse,
    LearningPreferencesUpsert,
)
from app.models.user import User
from app.services.learning_preferences_service import (
    LearningPreferencesUserNotFoundError,
    get_learning_preferences,
    save_learning_preferences,
)


router = APIRouter()


@router.get(
    "/users/{user_id}/learning-preferences",
    response_model=LearningPreferencesResponse,
)
def read_learning_preferences(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LearningPreferencesResponse:
    """Return saved preferences or defaults for a user."""
    try:
        require_current_user_id(user_id, current_user)
        return get_learning_preferences(
            user_id=user_id,
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
            detail="Learning preferences could not be loaded.",
        ) from error
@router.put(
    "/users/{user_id}/learning-preferences",
    response_model=LearningPreferencesResponse,
)
def upsert_learning_preferences(
    user_id: int,
    payload: LearningPreferencesUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LearningPreferencesResponse:
    """Create or replace a user's learning preferences."""
    try:
        require_current_user_id(user_id, current_user)
        return save_learning_preferences(
            user_id=user_id,
            payload=payload,
            session=db,
        )
    except LearningPreferencesUserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The specified user was not found.",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Learning preferences could not be saved.",
        ) from error
