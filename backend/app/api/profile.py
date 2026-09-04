from fastapi import APIRouter

from app.models.profile import CareerProfile
from app.services.profile_service import get_profile

router = APIRouter()


@router.get("/profile", response_model=CareerProfile)
def read_profile() -> CareerProfile:
    """Return the current career profile."""
    return get_profile()