from pydantic import BaseModel, Field

class ResumeUploadResponse(BaseModel):
    original_filename : str
    content_type : str
    stored_filename : str

class ResumeTextResponse(BaseModel):
    stored_filename : str
    text : str

class StructuredResume(BaseModel):
    name: str | None = None
    email: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)