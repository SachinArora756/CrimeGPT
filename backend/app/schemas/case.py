from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
import re
from app.models.case import CaseStatus


class CaseCreate(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    complainant_name: str = Field(min_length=2, max_length=200)
    complainant_contact: str | None = Field(default=None, max_length=20)
    complainant_address: str | None = Field(default=None, max_length=1000)
    accused_name: str | None = Field(default=None, max_length=200)
    incident_date: date | None = None
    incident_time: str | None = Field(default=None, max_length=10)
    incident_location: str | None = Field(default=None, max_length=500)
    description: str = Field(min_length=10, max_length=50000)
    offense_type: str | None = Field(default=None, max_length=100)
    station_id: str | None = Field(default=None, max_length=50)
    priority: str | None = Field(default="medium", max_length=20)
    victims: list[dict] | None = None
    accused_persons: list[dict] | None = None
    witnesses: list[dict] | None = None

    @field_validator("incident_time")
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Time must be in HH:MM format")
        return v

    @field_validator("complainant_contact")
    @classmethod
    def validate_contact(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = re.sub(r"[\s\-\+\(\)]", "", v)
        if not cleaned.isdigit() or len(cleaned) < 7:
            raise ValueError("Contact must be a valid phone number")
        return v


class CaseUpdate(BaseModel):
    title: str | None = None
    complainant_name: str | None = None
    complainant_contact: str | None = None
    complainant_address: str | None = None
    accused_name: str | None = None
    incident_date: date | None = None
    incident_time: str | None = None
    incident_location: str | None = None
    description: str | None = None
    status: CaseStatus | None = None
    priority: str | None = None
    assigned_officer_id: int | None = None
    investigation_team: list[int] | None = None
    sections_applied: list | None = None
    offense_type: str | None = None
    victims: list[dict] | None = None
    accused_persons: list[dict] | None = None
    witnesses: list[dict] | None = None


class CaseResponse(BaseModel):
    id: int
    public_id: str
    fir_number: str
    title: str | None = None
    complainant_name: str
    complainant_contact: str | None
    complainant_address: str | None
    accused_name: str | None
    incident_date: date | None
    incident_time: str | None
    incident_location: str | None
    description: str
    extracted_data: dict | None
    status: CaseStatus
    priority: str | None = "medium"
    assigned_officer_id: int | None
    created_by_id: int | None = None
    assigned_by_id: int | None = None
    investigation_team: list | None
    sections_applied: list | None
    offense_type: str | None
    station_id: str | None
    victims: list | None
    accused_persons: list | None
    witnesses: list | None
    ai_confidence: int | None = None
    risk_score: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    cases: list[CaseResponse]
    total: int
    page: int
    per_page: int
