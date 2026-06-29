from pydantic import BaseModel, Field
from datetime import datetime, date
from app.models.case import CaseStatus


class CaseCreate(BaseModel):
    complainant_name: str = Field(min_length=2, max_length=200)
    complainant_contact: str | None = None
    complainant_address: str | None = None
    accused_name: str | None = None
    incident_date: date | None = None
    incident_time: str | None = None
    incident_location: str | None = None
    description: str = Field(min_length=10)
    offense_type: str | None = None
    station_id: str | None = None


class CaseUpdate(BaseModel):
    complainant_name: str | None = None
    complainant_contact: str | None = None
    complainant_address: str | None = None
    accused_name: str | None = None
    incident_date: date | None = None
    incident_time: str | None = None
    incident_location: str | None = None
    description: str | None = None
    status: CaseStatus | None = None
    assigned_officer_id: int | None = None
    sections_applied: list | None = None
    offense_type: str | None = None


class CaseResponse(BaseModel):
    id: int
    fir_number: str
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
    assigned_officer_id: int | None
    sections_applied: list | None
    offense_type: str | None
    station_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    cases: list[CaseResponse]
    total: int
    page: int
    per_page: int
