from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Any

from app.models.criminal_intelligence import DangerLevel, WantedStatus, Gender


# ─── Criminal Profile Schemas ───────────────────────────────────────────────────

class CriminalProfileCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    father_name: str | None = Field(default=None, max_length=200)
    nicknames: list[str] | None = None
    date_of_birth: date | None = None
    gender: Gender = Gender.MALE
    nationality: str = "Indian"
    religion: str | None = Field(default=None, max_length=50)
    caste: str | None = Field(default=None, max_length=50)
    occupation: str | None = Field(default=None, max_length=100)
    education: str | None = Field(default=None, max_length=100)

    height_cm: float | None = None
    weight_kg: float | None = None
    build: str | None = Field(default=None, max_length=30)
    complexion: str | None = Field(default=None, max_length=30)
    hair_color: str | None = Field(default=None, max_length=30)
    eye_color: str | None = Field(default=None, max_length=30)
    identifying_marks: list[str] | None = None

    gang_name: str | None = Field(default=None, max_length=100)
    gang_role: str | None = Field(default=None, max_length=50)
    crime_categories: list[str] | None = None
    modus_operandi: str | None = None
    known_weapons: list[str] | None = None

    wanted_status: WantedStatus = WantedStatus.NOT_WANTED
    danger_level: DangerLevel = DangerLevel.LOW
    reward_amount: float | None = None

    total_arrests: int = 0
    total_convictions: int = 0
    total_firs: int = 0
    first_offense_date: date | None = None

    prison_history: list[dict] | None = None
    court_cases: list[dict] | None = None
    bail_status: str | None = Field(default=None, max_length=50)

    notes: str | None = None
    station_id: str | None = Field(default=None, max_length=50)


class CriminalProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    father_name: str | None = Field(default=None, max_length=200)
    nicknames: list[str] | None = None
    date_of_birth: date | None = None
    gender: Gender | None = None
    nationality: str | None = Field(default=None, max_length=50)
    religion: str | None = Field(default=None, max_length=50)
    caste: str | None = Field(default=None, max_length=50)
    occupation: str | None = Field(default=None, max_length=100)
    education: str | None = Field(default=None, max_length=100)

    height_cm: float | None = None
    weight_kg: float | None = None
    build: str | None = Field(default=None, max_length=30)
    complexion: str | None = Field(default=None, max_length=30)
    hair_color: str | None = Field(default=None, max_length=30)
    eye_color: str | None = Field(default=None, max_length=30)
    identifying_marks: list[str] | None = None

    gang_name: str | None = Field(default=None, max_length=100)
    gang_role: str | None = Field(default=None, max_length=50)
    crime_categories: list[str] | None = None
    modus_operandi: str | None = None
    known_weapons: list[str] | None = None

    wanted_status: WantedStatus | None = None
    danger_level: DangerLevel | None = None
    reward_amount: float | None = None

    total_arrests: int | None = None
    total_convictions: int | None = None
    total_firs: int | None = None
    first_offense_date: date | None = None
    last_known_activity: datetime | None = None

    prison_history: list[dict] | None = None
    court_cases: list[dict] | None = None
    bail_status: str | None = Field(default=None, max_length=50)

    notes: str | None = None
    station_id: str | None = Field(default=None, max_length=50)


class CriminalProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: str
    full_name: str
    father_name: str | None = None
    nicknames: Any | None = None
    date_of_birth: date | None = None
    gender: Gender
    nationality: str
    religion: str | None = None
    caste: str | None = None
    occupation: str | None = None
    education: str | None = None

    height_cm: float | None = None
    weight_kg: float | None = None
    build: str | None = None
    complexion: str | None = None
    hair_color: str | None = None
    eye_color: str | None = None
    identifying_marks: Any | None = None

    gang_name: str | None = None
    gang_role: str | None = None
    crime_categories: Any | None = None
    modus_operandi: str | None = None
    known_weapons: Any | None = None

    wanted_status: WantedStatus
    danger_level: DangerLevel
    reward_amount: float | None = None

    total_arrests: int
    total_convictions: int
    total_firs: int
    first_offense_date: date | None = None
    last_known_activity: datetime | None = None

    prison_history: Any | None = None
    court_cases: Any | None = None
    bail_status: str | None = None

    notes: str | None = None
    is_active: bool
    added_by: int
    station_id: str | None = None

    created_at: datetime
    updated_at: datetime


class CriminalProfileDetailResponse(CriminalProfileResponse):
    """Extended response with counts of related data."""
    face_embeddings_count: int = 0
    fingerprints_count: int = 0
    dna_profiles_count: int = 0
    aliases: list[dict] = []
    addresses: list[dict] = []
    vehicles: list[dict] = []
    phone_numbers: list[dict] = []
    social_accounts: list[dict] = []
    associates: list[dict] = []
    case_history: list[dict] = []
    images: list[dict] = []
    timeline: list[dict] = []


class CriminalProfileListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: str
    full_name: str
    nicknames: Any | None = None
    gender: Gender
    wanted_status: WantedStatus
    danger_level: DangerLevel
    gang_name: str | None = None
    total_arrests: int
    total_firs: int
    crime_categories: Any | None = None
    primary_image_url: str | None = None
    created_at: datetime


class CriminalProfileListResponse(BaseModel):
    items: list[CriminalProfileListItem]
    total: int
    page: int
    per_page: int


class CriminalStatsResponse(BaseModel):
    total: int
    wanted: int
    most_wanted: int
    by_danger_level: dict[str, int]
    top_gangs: list[dict[str, Any]]
    top_categories: list[dict[str, Any]]
    recent_additions: int


# ─── Associate Schemas ───────────────────────────────────────────────────────────

class AssociateCreate(BaseModel):
    associate_criminal_id: int | None = None
    associate_name: str = Field(..., min_length=2, max_length=200)
    relationship_type: str = Field(..., max_length=50)
    gang_connection: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class AssociateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    associate_criminal_id: int | None = None
    associate_name: str
    relationship_type: str
    gang_connection: str | None = None
    notes: str | None = None
    created_at: datetime


# ─── Case History Schemas ────────────────────────────────────────────────────────

class CaseHistoryCreate(BaseModel):
    fir_number: str | None = Field(default=None, max_length=50)
    case_type: str = Field(..., max_length=50)
    sections_applied: list[str] | None = None
    police_station: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    date_of_offense: date | None = None
    date_of_arrest: date | None = None
    court_name: str | None = Field(default=None, max_length=200)
    case_status: str | None = Field(default=None, max_length=30)
    verdict: str | None = Field(default=None, max_length=50)
    sentence: str | None = Field(default=None, max_length=200)
    bail_granted: bool = False
    description: str | None = None


class CaseHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    fir_number: str | None = None
    case_type: str
    sections_applied: Any | None = None
    police_station: str | None = None
    district: str | None = None
    state: str | None = None
    date_of_offense: date | None = None
    date_of_arrest: date | None = None
    court_name: str | None = None
    case_status: str | None = None
    verdict: str | None = None
    sentence: str | None = None
    bail_granted: bool
    description: str | None = None
    created_at: datetime


# ─── Timeline Schemas ────────────────────────────────────────────────────────────

class TimelineCreate(BaseModel):
    event_date: date
    event_type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    description: str | None = None
    location: str | None = Field(default=None, max_length=200)
    metadata: dict | None = None


class TimelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    event_date: date
    event_type: str
    title: str
    description: str | None = None
    location: str | None = None
    metadata: Any | None = Field(default=None, validation_alias="extra_data")
    created_at: datetime


# ─── Address Schemas ─────────────────────────────────────────────────────────────

class AddressCreate(BaseModel):
    address_type: str = Field(..., max_length=30)
    address_line: str = Field(..., max_length=500)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=10)
    is_current: bool = True
    verified: bool = False


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    address_type: str
    address_line: str
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    is_current: bool
    verified: bool
    last_verified: datetime | None = None
    created_at: datetime


# ─── Vehicle Schemas ─────────────────────────────────────────────────────────────

class VehicleCreate(BaseModel):
    vehicle_type: str = Field(..., max_length=30)
    make: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=30)
    registration_number: str | None = Field(default=None, max_length=20)
    chassis_number: str | None = Field(default=None, max_length=50)
    is_stolen: bool = False
    notes: str | None = None


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    vehicle_type: str
    make: str | None = None
    model: str | None = None
    color: str | None = None
    registration_number: str | None = None
    chassis_number: str | None = None
    is_stolen: bool
    notes: str | None = None
    created_at: datetime


# ─── Watchlist Schemas ───────────────────────────────────────────────────────────

class WatchlistCreate(BaseModel):
    criminal_id: int
    reason: str = Field(..., min_length=5)
    priority: str = Field(default="medium", max_length=20)
    alert_on_match: bool = True
    expires_at: datetime | None = None


class WatchlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    criminal_name: str | None = None
    criminal_profile_id: str | None = None
    added_by: int
    reason: str
    priority: str
    alert_on_match: bool
    is_active: bool
    expires_at: datetime | None = None
    created_at: datetime


# ─── Search Log Schema ───────────────────────────────────────────────────────────

class SearchLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    search_type: str
    search_query: str | None = None
    input_file_path: str | None = None
    results_count: int
    top_match_id: int | None = None
    top_match_confidence: float | None = None
    ip_address: str | None = None
    execution_time_ms: int | None = None
    created_at: datetime


# ─── Biometric Schemas ──────────────────────────────────────────────────────────

class FaceEmbeddingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    image_path: str
    model_name: str
    embedding_dim: int
    quality_score: float | None = None
    created_at: datetime


class FingerprintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    finger_type: str
    image_path: str | None = None
    quality_score: float | None = None
    created_at: datetime


class DNAProfileCreate(BaseModel):
    dna_id: str = Field(..., min_length=1, max_length=50)
    sample_number: str | None = Field(default=None, max_length=50)
    laboratory: str | None = Field(default=None, max_length=200)
    collection_date: date | None = None
    profile_data: dict | None = None
    loci_markers: dict | None = None


class DNAProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    dna_id: str
    sample_number: str | None = None
    laboratory: str | None = None
    collection_date: date | None = None
    profile_data: Any | None = None
    loci_markers: Any | None = None
    created_at: datetime
