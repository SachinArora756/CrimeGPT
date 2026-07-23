import enum
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Text, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocType(str, enum.Enum):
    FIR = "fir"
    CHARGESHEET = "chargesheet"
    SEIZURE_MEMO = "seizure_memo"
    MEDICAL_LETTER = "medical_letter"
    COURT_LETTER = "court_letter"
    ARREST_MEMO = "arrest_memo"
    CASE_DIARY = "case_diary"
    WITNESS_STATEMENT = "witness_statement"
    SEARCH_MEMO = "search_memo"
    NOTICE = "notice"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    doc_type: Mapped[DocType] = mapped_column(SAEnum(DocType, native_enum=False, length=30))
    output_format: Mapped[str] = mapped_column(String(10), default="docx")
    file_path: Mapped[str] = mapped_column(String(500))
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generated_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case = relationship("Case", foreign_keys=[case_id])
    generator = relationship("User", foreign_keys=[generated_by])


class CaseDiary(Base):
    __tablename__ = "case_diary"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    entry_date: Mapped[date] = mapped_column(Date)
    content: Mapped[str] = mapped_column(Text)
    entry_type: Mapped[str] = mapped_column(String(50), default="investigation")
    officer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", foreign_keys=[case_id])
    officer = relationship("User", foreign_keys=[officer_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(50))
    resource_type: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[dict | None] = mapped_column(type_=JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
