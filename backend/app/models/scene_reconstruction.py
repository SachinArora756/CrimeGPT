from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SceneReconstruction(Base):
    __tablename__ = "scene_reconstructions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    reconstruction_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    status: Mapped[str] = mapped_column(String(20), default="pending")
    scene_layout: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timeline_events: Mapped[list | None] = mapped_column(JSON, nullable=True)
    objects_placed: Mapped[list | None] = mapped_column(JSON, nullable=True)
    photo_textures: Mapped[list | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    export_html_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    export_video_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    generated_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", foreign_keys=[case_id])
    generator = relationship("User", foreign_keys=[generated_by])
