from pydantic import BaseModel, Field


class SkillExtractionResult(BaseModel):
    skills: list[str] = Field(default_factory=list)