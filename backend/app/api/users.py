from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter()


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Create a new CareerLens user."""
    user_service = UserService(db)

    try:
        user = user_service.create_user(
            email=user_data.email,
            name=user_data.name,
        )
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from error

    return UserResponse.model_validate(user)


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Retrieve a user by ID."""
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return UserResponse.model_validate(user)