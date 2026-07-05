import enum
import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Text, ForeignKey, JSON, Integer, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CaseStatus(str, enum.Enum):
    REGISTERED = "registered"
    INVESTIGATING = "investigating"
    CHARGESHEET_FILED = "chargesheet_filed"
    CLOSED = "closed"


class CasePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    fir_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    complainant_name: Mapped[str] = mapped_column(String(200))
    complainant_contact: Mapped[str | None] = mapped_column(String(20), nullable=True)
    complainant_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    accused_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    incident_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    incident_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    incident_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text)
    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[CaseStatus] = mapped_column(SAEnum(CaseStatus, native_enum=False, length=30), default=CaseStatus.REGISTERED, index=True)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True, default="medium")
    assigned_officer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assigned_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    investigation_team: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sections_applied: Mapped[list | None] = mapped_column(JSON, nullable=True)
    offense_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    station_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    victims: Mapped[list | None] = mapped_column(JSON, nullable=True)
    accused_persons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    witnesses: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ai_confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    officer = relationship("User", foreign_keys=[assigned_officer_id])
    creator = relationship("User", foreign_keys=[created_by_id])
    assigner = relationship("User", foreign_keys=[assigned_by_id])
