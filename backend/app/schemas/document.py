from pydantic import BaseModel
from datetime import datetime, date
from app.models.document import DocType


class DocumentGenerateRequest(BaseModel):
    doc_type: DocType
    additional_context: str | None = None


class DocumentResponse(BaseModel):
    id: int
    case_id: int
    doc_type: DocType
    file_path: str
    generated_by: int
    generated_at: datetime

    class Config:
        from_attributes = True


class CaseDiaryCreate(BaseModel):
    entry_date: date
    content: str
    entry_type: str = "investigation"


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
