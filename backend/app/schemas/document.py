from typing import Literal
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime, date
from app.models.document import DocType


class DocumentGenerateRequest(BaseModel):
    doc_type: DocType
    additional_context: str | None = Field(default=None, max_length=5000)
    output_format: Literal["docx", "pdf"] = "pdf"


class DocumentResponse(BaseModel):
    id: int
    case_id: int
    doc_type: DocType
    output_format: str = "pdf"
    file_path: str
    file_hash: str | None = None
    generated_by: int
    generated_at: datetime

    @field_serializer('generated_at')
    def serialize_generated_at(self, v: datetime) -> str | None:
        if not v:
            return None
        return v.isoformat() + "Z"

    class Config:
        from_attributes = True


class CaseDiaryCreate(BaseModel):
    entry_date: date
    content: str = Field(min_length=1, max_length=50000)
    entry_type: Literal[
        "investigation", "arrest", "search", "seizure", "forensic", "witness", "other",
        "investigation_step", "evidence_collected", "witness_statement", "arrest_details",
        "court_appearance", "supervisor_note",
    ] = "investigation_step"


class CaseDiaryResponse(BaseModel):
    id: int
    case_id: int
    entry_date: date
    content: str
    entry_type: str
    officer_id: int
    is_auto: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class DiarySummaryRequest(BaseModel):
    target_date: date | None = None
