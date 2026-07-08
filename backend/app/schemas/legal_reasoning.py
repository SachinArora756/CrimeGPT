from pydantic import BaseModel, Field
from datetime import datetime


class SectionRecommendation(BaseModel):
    section: str
    act: str
    title: str
    explanation: str
    supporting_evidence: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    punishment_range: str = ""
    is_primary: bool = True


class RecommendationResponse(BaseModel):
    id: int
    case_id: int
    recommendations: list[SectionRecommendation]
    procedural_notes: list[str] = []
    evidence_gaps: list[str] = []
    overall_confidence: float
    status: str
    approved_sections: list[str] | None = None
    officer_notes: str | None = None
    approved_by: int | None = None
    approved_at: datetime | None = None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalRequest(BaseModel):
    approved_sections: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=2000)


class RecommendationGenerateRequest(BaseModel):
    focus_area: str | None = Field(default=None, max_length=500)


class LegalChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


class LegalChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
