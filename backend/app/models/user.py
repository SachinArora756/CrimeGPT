import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Integer, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    COMMISSIONER = "commissioner"
    ACP = "acp"
    SHO = "sho"
    INSPECTOR = "inspector"
    SUB_INSPECTOR = "sub_inspector"
    CONSTABLE = "constable"


ROLE_HIERARCHY = {
    UserRole.SUPER_ADMIN: 7,
    UserRole.COMMISSIONER: 6,
    UserRole.ACP: 5,
    UserRole.SHO: 4,
    UserRole.INSPECTOR: 3,
    UserRole.SUB_INSPECTOR: 2,
    UserRole.CONSTABLE: 1,
}


def is_higher_or_equal(role_a: UserRole, role_b: UserRole) -> bool:
    return ROLE_HIERARCHY[role_a] >= ROLE_HIERARCHY[role_b]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, native_enum=False, length=20), default=UserRole.CONSTABLE)
    station_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    badge_number: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Security fields
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    account_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    force_password_change: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_picture: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
