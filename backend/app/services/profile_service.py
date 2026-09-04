from app.models.profile import CareerProfile


_profile = CareerProfile(
    name="CareerLens User",
    target_role="Software Developer",
    skills=["Python", "FastAPI", "React"],
)


def get_profile() -> CareerProfile:
    """Return the current in-memory career profile."""
    return _profile