import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from app.models.user import UserRole


COMMON_PASSWORDS = {
    "password123", "12345678", "qwerty123", "admin1234", "letmein123",
    "welcome123", "monkey1234", "dragon1234", "master1234", "login12345",
    "abc12345678", "password1234", "123456789", "1234567890", "qwerty1234",
    "iloveyou123", "princess123", "football123", "shadow1234", "sunshine123",
    "trustno1234", "passw0rd123", "whatever123", "freedom1234", "hello12345",
    "charlie1234", "donald1234", "batman1234", "access1234", "thunder1234",
    "police1234", "officer1234", "constable123", "inspector123", "crimegpt123",
}


def validate_password_strength(v: str) -> str:
    if len(v) < 10:
        raise ValueError("Password must be at least 10 characters long")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:'\",.<>?/\\~`]", v):
        raise ValueError("Password must contain at least one special character (!@#$%^&*...)")
    if re.search(r"(.)\1{2,}", v):
        raise ValueError("Password must not contain 3 or more repeating characters")
    if v.lower() in COMMON_PASSWORDS:
        raise ValueError("This password is too common. Please choose a stronger one")
    return v


class AdminUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=100)
    role: UserRole = UserRole.CONSTABLE
    station_id: str | None = Field(default=None, max_length=50)
    department: str | None = Field(default=None, max_length=100)
    badge_number: str | None = Field(default=None, max_length=50)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return validate_password_strength(v)


class AdminUserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None
    station_id: str | None = None
    department: str | None = None
    badge_number: str | None = None
    is_active: bool | None = None


class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=10, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return validate_password_strength(v)


class UserListResponse(BaseModel):
    users: list["UserDetailResponse"]
    total: int
    page: int
    per_page: int


class UserDetailResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    station_id: str | None
    department: str | None
    badge_number: str | None
    is_active: bool
    failed_login_attempts: int = 0
    account_locked: bool = False
    last_login: datetime | None = None
    password_changed_at: datetime | None = None
    force_password_change: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class SystemStats(BaseModel):
    total_users: int
    active_users: int
    total_cases: int
    cases_by_status: dict[str, int]
    total_evidence: int
    total_documents: int


class SystemHealth(BaseModel):
    database: str
    qdrant: str
    storage: str
