import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    INSPECTOR = "inspector"
    SUB_INSPECTOR = "sub_inspector"
    CONSTABLE = "constable"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.CONSTABLE)
    station_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    badge_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
