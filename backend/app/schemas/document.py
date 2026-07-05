from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime, date
from app.models.document import DocType


class DocumentGenerateRequest(BaseModel):
    doc_type: DocType
    additional_context: str | None = Field(default=None, max_length=5000)
    output_format: Literal["docx", "pdf"] = "docx"


class DocumentResponse(BaseModel):
    id: int
    case_id: int
    doc_type: DocType
    output_format: str = "docx"
    file_path: str
    generated_by: int
    generated_at: datetime

    class Config:
        from_attributes = True


class CaseDiaryCreate(BaseModel):
    entry_date: date
    content: str = Field(min_length=1, max_length=50000)
    entry_type: Literal["investigation", "arrest", "search", "seizure", "forensic", "witness", "other"] = "investigation"


class CaseDiaryResponse(BaseModel):
    id: int
    case_id: int
    entry_date: date
    content: str
    entry_type: str
    officer_id: int
    created_at: datetime

    class Config:
        from_attributes = True
