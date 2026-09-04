from pydantic import BaseModel

class ResumeUploadResponse(BaseModel):
    original_filename : str
    content_type : str
    stored_filename : str

class ResumeTextResponse(BaseModel):
    stored_filename : str
    text : str