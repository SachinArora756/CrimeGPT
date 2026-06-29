from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    file_path: Mapped[str] = mapped_column(String(500))
    original_filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(50))
    file_size: Mapped[int] = mapped_column(Integer)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case = relationship("Case", foreign_keys=[case_id])
    uploader = relationship("User", foreign_keys=[uploaded_by])
