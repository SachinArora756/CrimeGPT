from typing import Literal
from pydantic import BaseModel, field_serializer
from datetime import datetime


class ReportReadinessResponse(BaseModel):
    ready: bool
    case_status: str
    completeness_score: int
    missing_items: list[str]
    message: str


class ReportGenerateRequest(BaseModel):
    output_format: Literal["docx", "pdf"] = "pdf"


class ReportGenerateResponse(BaseModel):
    id: int
    case_id: int
    file_path: str
    file_hash: str | None = None
    generated_by: int
    generated_at: datetime
    output_format: str
    sections_generated: int

    @field_serializer('generated_at')
    def serialize_generated_at(self, v: datetime) -> str | None:
        if not v:
            return None
        return v.isoformat() + "Z"

    class Config:
        from_attributes = True


class ReportListItem(BaseModel):
    id: int
    case_id: int
    file_hash: str | None = None
    generated_by: int
    generated_at: datetime
    output_format: str

    @field_serializer('generated_at')
    def serialize_generated_at(self, v: datetime) -> str | None:
        if not v:
            return None
        return v.isoformat() + "Z"

    class Config:
        from_attributes = True
