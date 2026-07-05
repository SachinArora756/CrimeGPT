from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IngestionLog(Base):
    __tablename__ = "ingestion_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    file_hash: Mapped[str] = mapped_column(String(64))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    collection_name: Mapped[str] = mapped_column(String(100), default="legal_provisions")
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default=None)
    uploaded_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default=None)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default=None)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    embedding_model: Mapped[str] = mapped_column(String(100), default="BAAI/bge-small-en-v1.5", server_default="BAAI/bge-small-en-v1.5")


class KBActivityLog(Base):
    __tablename__ = "kb_activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    document_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    collection_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
