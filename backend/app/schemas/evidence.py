from pydantic import BaseModel
from datetime import datetime


class EvidenceResponse(BaseModel):
    id: int
    case_id: int
    file_path: str
    original_filename: str
    file_type: str
    file_size: int
    file_hash: str | None
    ocr_text: str | None
    analysis_results: dict | None
    description: str | None
    tags: list | None
    chain_of_custody: list | None
    uploaded_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class EvidenceListResponse(BaseModel):
    evidence: list[EvidenceResponse]
    total: int
