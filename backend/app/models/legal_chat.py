from datetime import datetime
from sqlalchemy import DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.database import Base
from app.models.chat import ChatRole


class LegalChatMessage(Base):
    __tablename__ = "legal_chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("legal_recommendations.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[ChatRole] = mapped_column(SAEnum(ChatRole, native_enum=False, length=15))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case = relationship("Case", foreign_keys=[case_id])
    user = relationship("User", foreign_keys=[user_id])
    recommendation = relationship("LegalRecommendation", foreign_keys=[recommendation_id])
