import enum
from datetime import datetime
from sqlalchemy import (
    String, DateTime, Boolean, Integer, Float, Text,
    Enum as SAEnum, ForeignKey, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ForensicToolDefinition(Base):
    __tablename__ = "forensic_tool_definitions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tool_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    accepted_file_types: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    max_file_size_mb: Mapped[int] = mapped_column(Integer, default=50)
    requires_case: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ForensicToolExecution(Base):
    __tablename__ = "forensic_tool_executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    execution_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    tool_key: Mapped[str] = mapped_column(String(80), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)
    evidence_id: Mapped[int | None] = mapped_column(ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[ExecutionStatus] = mapped_column(
        SAEnum(ExecutionStatus, native_enum=False, length=20), default=ExecutionStatus.PENDING
    )
    input_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    input_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    input_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User")


class ForensicSavedResult(Base):
    __tablename__ = "forensic_saved_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("forensic_tool_executions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=True)
    linked_case_id: Mapped[int | None] = mapped_column(ForeignKey("cases.id", ondelete="SET NULL"), nullable=True)
    linked_evidence_id: Mapped[int | None] = mapped_column(ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    execution = relationship("ForensicToolExecution")
