from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AIInvestigationSession(Base):
    __tablename__ = "ai_investigation_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(300), default="New Investigation")
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    messages = relationship(
        "AIInvestigationMessage",
        back_populates="session",
        order_by="AIInvestigationMessage.created_at",
        cascade="all, delete-orphan",
    )


class AIInvestigationMessage(Base):
    __tablename__ = "ai_investigation_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    message_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("ai_investigation_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(15))
    content: Mapped[str] = mapped_column(Text, default="")
    attachments: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tool_executions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session = relationship("AIInvestigationSession", back_populates="messages")
