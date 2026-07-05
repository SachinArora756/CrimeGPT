import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.database import Base


class TimelineEventType(str, enum.Enum):
    CASE_CREATED = "case_created"
    STATUS_CHANGED = "status_changed"
    EVIDENCE_UPLOADED = "evidence_uploaded"
    DOCUMENT_GENERATED = "document_generated"
    OFFICER_ASSIGNED = "officer_assigned"
    NOTE_ADDED = "note_added"
    INVESTIGATION_UPDATE = "investigation_update"


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[TimelineEventType] = mapped_column(
        SAEnum(TimelineEventType, native_enum=False, length=30)
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(type_=JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case = relationship("Case", foreign_keys=[case_id])
    actor = relationship("User", foreign_keys=[actor_id])
