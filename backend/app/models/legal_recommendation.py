import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, Float, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RecommendationStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PARTIALLY_APPROVED = "partially_approved"
    REJECTED = "rejected"


class LegalRecommendation(Base):
    __tablename__ = "legal_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    recommendations: Mapped[dict] = mapped_column(JSON)
    overall_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[RecommendationStatus] = mapped_column(
        SAEnum(RecommendationStatus, native_enum=False, length=30),
        default=RecommendationStatus.PENDING_APPROVAL,
        index=True,
    )
    approved_sections: Mapped[list | None] = mapped_column(JSON, nullable=True)
    officer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", foreign_keys=[case_id])
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])
