"""Investigation Memory and Cross-Evidence Correlation models."""

from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, Float, Integer, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class InvestigationMemory(Base):
    __tablename__ = "investigation_memory"
    __table_args__ = (
        Index("ix_inv_memory_case_type", "case_id", "finding_type"),
        Index("ix_inv_memory_case_key", "case_id", "finding_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    evidence_id: Mapped[int] = mapped_column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), index=True)
    finding_type: Mapped[str] = mapped_column(String(50))
    finding_key: Mapped[str] = mapped_column(String(255))
    finding_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvidenceCorrelation(Base):
    __tablename__ = "evidence_correlations"
    __table_args__ = (
        Index("ix_ev_corr_case", "case_id"),
        Index("ix_ev_corr_source", "source_evidence_id"),
        Index("ix_ev_corr_target", "target_evidence_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    source_evidence_id: Mapped[int] = mapped_column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"))
    target_evidence_id: Mapped[int] = mapped_column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"))
    correlation_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
