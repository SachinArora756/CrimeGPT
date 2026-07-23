import enum
from datetime import datetime, date
from sqlalchemy import (
    String, DateTime, Date, Boolean, Integer, Float, Text,
    Enum as SAEnum, ForeignKey, JSON, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DangerLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class WantedStatus(str, enum.Enum):
    NOT_WANTED = "not_wanted"
    WANTED = "wanted"
    MOST_WANTED = "most_wanted"
    SURRENDERED = "surrendered"
    ARRESTED = "arrested"
    ABSCONDING = "absconding"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class CriminalProfile(Base):
    __tablename__ = "criminal_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), index=True)
    father_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    nicknames: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[Gender] = mapped_column(SAEnum(Gender, native_enum=False, length=10), default=Gender.MALE)
    nationality: Mapped[str] = mapped_column(String(50), default="Indian")
    religion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    caste: Mapped[str | None] = mapped_column(String(50), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    education: Mapped[str | None] = mapped_column(String(100), nullable=True)

    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    build: Mapped[str | None] = mapped_column(String(30), nullable=True)
    complexion: Mapped[str | None] = mapped_column(String(30), nullable=True)
    hair_color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    eye_color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    identifying_marks: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    gang_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    gang_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    crime_categories: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    modus_operandi: Mapped[str | None] = mapped_column(Text, nullable=True)
    known_weapons: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    wanted_status: Mapped[WantedStatus] = mapped_column(
        SAEnum(WantedStatus, native_enum=False, length=20), default=WantedStatus.NOT_WANTED
    )
    danger_level: Mapped[DangerLevel] = mapped_column(
        SAEnum(DangerLevel, native_enum=False, length=10), default=DangerLevel.LOW
    )
    reward_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    total_arrests: Mapped[int] = mapped_column(Integer, default=0)
    total_convictions: Mapped[int] = mapped_column(Integer, default=0)
    total_firs: Mapped[int] = mapped_column(Integer, default=0)
    first_offense_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_known_activity: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    prison_history: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    court_cases: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bail_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    added_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    station_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    last_known_state: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    last_known_district: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    marked_most_wanted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    marked_most_wanted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    gang_marked_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    gang_marked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    face_embeddings = relationship("CriminalFaceEmbedding", back_populates="criminal", cascade="all, delete-orphan")
    fingerprints = relationship("CriminalFingerprint", back_populates="criminal", cascade="all, delete-orphan")
    dna_profiles = relationship("CriminalDNAProfile", back_populates="criminal", cascade="all, delete-orphan")
    aliases = relationship("CriminalAlias", back_populates="criminal", cascade="all, delete-orphan")
    addresses = relationship("CriminalAddress", back_populates="criminal", cascade="all, delete-orphan")
    vehicles = relationship("CriminalVehicle", back_populates="criminal", cascade="all, delete-orphan")
    phone_numbers = relationship("CriminalPhoneNumber", back_populates="criminal", cascade="all, delete-orphan")
    social_accounts = relationship("CriminalSocialAccount", back_populates="criminal", cascade="all, delete-orphan")
    associates = relationship("CriminalAssociate", back_populates="criminal", foreign_keys="CriminalAssociate.criminal_id", cascade="all, delete-orphan")
    case_history = relationship("CriminalCaseHistory", back_populates="criminal", cascade="all, delete-orphan")
    images = relationship("CriminalImage", back_populates="criminal", cascade="all, delete-orphan")
    documents = relationship("CriminalDocument", back_populates="criminal", cascade="all, delete-orphan")
    timelines = relationship("CriminalTimeline", back_populates="criminal", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_criminal_profiles_wanted_danger", "wanted_status", "danger_level"),
        Index("ix_criminal_profiles_gang", "gang_name"),
        Index("ix_criminal_profiles_location", "last_known_state", "last_known_district"),
    )


class CriminalFaceEmbedding(Base):
    __tablename__ = "criminal_face_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    embedding: Mapped[dict] = mapped_column(JSON)
    image_path: Mapped[str] = mapped_column(String(500))
    model_name: Mapped[str] = mapped_column(String(50), default="insightface_buffalo")
    embedding_dim: Mapped[int] = mapped_column(Integer, default=512)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="face_embeddings")


class CriminalFingerprint(Base):
    __tablename__ = "criminal_fingerprints"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    finger_type: Mapped[str] = mapped_column(String(30))
    template_data: Mapped[dict] = mapped_column(JSON)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="fingerprints")


class CriminalDNAProfile(Base):
    __tablename__ = "criminal_dna_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    dna_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    sample_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    laboratory: Mapped[str | None] = mapped_column(String(200), nullable=True)
    collection_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    profile_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    loci_markers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="dna_profiles")


class CriminalAlias(Base):
    __tablename__ = "criminal_aliases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    alias_name: Mapped[str] = mapped_column(String(200), index=True)
    context: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="aliases")


class CriminalAddress(Base):
    __tablename__ = "criminal_addresses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    address_type: Mapped[str] = mapped_column(String(30))
    address_line: Mapped[str] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_verified: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="addresses")


class CriminalVehicle(Base):
    __tablename__ = "criminal_vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    vehicle_type: Mapped[str] = mapped_column(String(30))
    make: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    chassis_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_stolen: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="vehicles")


class CriminalPhoneNumber(Base):
    __tablename__ = "criminal_phone_numbers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    phone_number: Mapped[str] = mapped_column(String(20), index=True)
    phone_type: Mapped[str] = mapped_column(String(20), default="mobile")
    carrier: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    registered_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="phone_numbers")


class CriminalSocialAccount(Base):
    __tablename__ = "criminal_social_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(50))
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    profile_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="social_accounts")


class CriminalAssociate(Base):
    __tablename__ = "criminal_associates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    associate_criminal_id: Mapped[int | None] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="SET NULL"), nullable=True)
    associate_name: Mapped[str] = mapped_column(String(200))
    relationship_type: Mapped[str] = mapped_column(String(50))
    gang_connection: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="associates", foreign_keys=[criminal_id])
    associate_profile = relationship("CriminalProfile", foreign_keys=[associate_criminal_id])


class CriminalCaseHistory(Base):
    __tablename__ = "criminal_case_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    fir_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    case_type: Mapped[str] = mapped_column(String(50))
    sections_applied: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    police_station: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_offense: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_of_arrest: Mapped[date | None] = mapped_column(Date, nullable=True)
    court_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    case_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    verdict: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sentence: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bail_granted: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="case_history")


class CriminalImage(Base):
    __tablename__ = "criminal_images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    image_path: Mapped[str] = mapped_column(String(500))
    image_type: Mapped[str] = mapped_column(String(30))
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="images")


class CriminalDocument(Base):
    __tablename__ = "criminal_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    doc_type: Mapped[str] = mapped_column(String(50))
    file_path: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="documents")


class CriminalTimeline(Base):
    __tablename__ = "criminal_timelines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="CASCADE"), index=True)
    event_date: Mapped[date] = mapped_column(Date)
    event_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    extra_data: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    criminal = relationship("CriminalProfile", back_populates="timelines")


class CriminalSearchLog(Base):
    __tablename__ = "criminal_search_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    search_type: Mapped[str] = mapped_column(String(30))
    search_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    results_count: Mapped[int] = mapped_column(Integer, default=0)
    top_match_id: Mapped[int | None] = mapped_column(ForeignKey("criminal_profiles.id", ondelete="SET NULL"), nullable=True)
    top_match_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OsintIdentifierType(str, enum.Enum):
    PHONE = "phone"
    EMAIL = "email"
    USERNAME = "username"
    VEHICLE_PLATE = "vehicle_plate"
    IP_DOMAIN = "ip_domain"
    PERSON_NAME = "person_name"


class OsintFindingStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"


class OsintInvestigation(Base):
    __tablename__ = "osint_investigations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    identifier_type: Mapped[OsintIdentifierType] = mapped_column(
        SAEnum(OsintIdentifierType, native_enum=False, length=20)
    )
    identifier_value: Mapped[str] = mapped_column(String(500), index=True)
    findings: Mapped[dict] = mapped_column(JSON)
    officer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_status: Mapped[OsintFindingStatus] = mapped_column(
        SAEnum(OsintFindingStatus, native_enum=False, length=20),
        default=OsintFindingStatus.UNVERIFIED,
    )
    finding_statuses: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    linked_criminal_id: Mapped[int | None] = mapped_column(
        ForeignKey("criminal_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    searched_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    ai_model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_generation_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_osint_investigations_type_value", "identifier_type", "identifier_value"),
    )
