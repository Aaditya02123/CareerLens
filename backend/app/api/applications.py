from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatusUpdate,
)
from app.services.application_service import (
    ApplicationNotFoundError,
    ApplicationService,
    DuplicateApplicationError,
    JobNotFoundError,
    UserNotFoundError,
)

router = APIRouter()


@router.post(
    "/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    application_data: ApplicationCreate,
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Create a tracked job application."""
    service = ApplicationService(db)

    try:
        application = service.create_application(application_data)
    except (UserNotFoundError, JobNotFoundError) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except DuplicateApplicationError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This application already exists.",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The application could not be created.",
        ) from error

    return ApplicationResponse.model_validate(application)


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Retrieve a tracked application."""
    service = ApplicationService(db)

    try:
        application = service.get_application(application_id)
    except ApplicationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The application could not be retrieved.",
        ) from error

    return ApplicationResponse.model_validate(application)


@router.get(
    "/users/{user_id}/applications",
    response_model=list[ApplicationResponse],
)
def list_user_applications(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[ApplicationResponse]:
    """List all applications tracked by a user."""
    service = ApplicationService(db)

    try:
        applications = service.list_applications_for_user(user_id)
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The applications could not be retrieved.",
        ) from error

    return [
        ApplicationResponse.model_validate(application)
        for application in applications
    ]


@router.patch(
    "/applications/{application_id}/status",
    response_model=ApplicationResponse,
)
def update_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
) -> ApplicationResponse:
    """Update the status of a tracked application."""
    service = ApplicationService(db)

    try:
        application = service.update_application_status(
            application_id=application_id,
            new_status=status_data.status,
        )
    except ApplicationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The application status could not be updated.",
        ) from error

    return ApplicationResponse.model_validate(application)