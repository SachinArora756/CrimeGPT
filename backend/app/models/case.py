import enum
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Text, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CaseStatus(str, enum.Enum):
    REGISTERED = "registered"
    INVESTIGATING = "investigating"
    CHARGESHEET_FILED = "chargesheet_filed"
    CLOSED = "closed"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fir_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    complainant_name: Mapped[str] = mapped_column(String(200))
    complainant_contact: Mapped[str | None] = mapped_column(String(20), nullable=True)
    complainant_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    accused_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    incident_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    incident_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    incident_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text)
    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[CaseStatus] = mapped_column(SAEnum(CaseStatus), default=CaseStatus.REGISTERED)
    assigned_officer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    sections_applied: Mapped[list | None] = mapped_column(JSON, nullable=True)
    offense_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    station_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    officer = relationship("User", foreign_keys=[assigned_officer_id])
