from pydantic import BaseModel


class CareerProfile(BaseModel):
    name: str
    target_role: str
    skills: list[str]