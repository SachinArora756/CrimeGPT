from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ForensicPhoto(Base):
    __tablename__ = "forensic_photos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    photo_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    evidence_id: Mapped[int | None] = mapped_column(ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True)

    file_path: Mapped[str] = mapped_column(String(500))
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer)
    file_hash_sha256: Mapped[str] = mapped_column(String(64))
    mime_type: Mapped[str] = mapped_column(String(50))

    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    exif_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    gps_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    capture_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    device_make: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scene_zone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_assessment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_detected_objects: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    courtroom_readiness: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_suggestions: Mapped[list | None] = mapped_column(JSON, nullable=True)

    capture_source: Mapped[str] = mapped_column(String(20), default="upload")
    is_original: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_photo_id: Mapped[int | None] = mapped_column(ForeignKey("forensic_photos.id", ondelete="SET NULL"), nullable=True)
    chain_of_custody: Mapped[list | None] = mapped_column(JSON, nullable=True)
    section_65b_certificate: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", foreign_keys=[case_id])
    uploader = relationship("User", foreign_keys=[uploaded_by])
    annotations = relationship("PhotoAnnotation", back_populates="photo", cascade="all, delete-orphan")
    parent = relationship("ForensicPhoto", remote_side=[id], foreign_keys=[parent_photo_id])


class PhotoAnnotation(Base):
    __tablename__ = "photo_annotations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    photo_id: Mapped[int] = mapped_column(ForeignKey("forensic_photos.id", ondelete="CASCADE"), index=True)

    annotation_type: Mapped[str] = mapped_column(String(30))
    canvas_data: Mapped[dict] = mapped_column(JSON)
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    evidence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    photo = relationship("ForensicPhoto", back_populates="annotations")
    creator = relationship("User", foreign_keys=[created_by])


class SceneCoverageZone(Base):
    __tablename__ = "scene_coverage_zones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)

    zone_key: Mapped[str] = mapped_column(String(50))
    zone_label: Mapped[str] = mapped_column(String(100))
    required_shots: Mapped[int] = mapped_column(Integer, default=3)
    actual_shots: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(10), default="red")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", foreign_keys=[case_id])


class PhotoEnhancementHistory(Base):
    __tablename__ = "photo_enhancement_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    original_photo_id: Mapped[int] = mapped_column(ForeignKey("forensic_photos.id", ondelete="CASCADE"), index=True)
    enhanced_photo_id: Mapped[int | None] = mapped_column(ForeignKey("forensic_photos.id", ondelete="SET NULL"), nullable=True)

    enhancement_type: Mapped[str] = mapped_column(String(50))
    parameters: Mapped[dict] = mapped_column(JSON)

    performed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    original_photo = relationship("ForensicPhoto", foreign_keys=[original_photo_id])
    enhanced_photo = relationship("ForensicPhoto", foreign_keys=[enhanced_photo_id])
    performer = relationship("User", foreign_keys=[performed_by])
