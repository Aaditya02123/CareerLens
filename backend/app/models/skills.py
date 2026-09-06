from enum import Enum

from pydantic import BaseModel, Field


class SkillCategory(str, Enum):
    PROGRAMMING_LANGUAGE = "Programming Language"
    FRAMEWORK_LIBRARY = "Framework / Library"
    DATABASE = "Database"
    CLOUD = "Cloud"
    DEVOPS_INFRASTRUCTURE = "DevOps / Infrastructure"
    AI_ML = "AI / ML"
    TOOLS = "Tools"
    CORE_CS = "Core CS"
    OTHER = "Other"


class Skill(BaseModel):
    name: str
    category: SkillCategory


class SkillExtractionResult(BaseModel):
    skills: list[str] = Field(default_factory=list)


class CategorizedSkillResult(BaseModel):
    skills: list[Skill] = Field(default_factory=list)