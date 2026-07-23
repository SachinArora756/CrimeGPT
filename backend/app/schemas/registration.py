from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from datetime import datetime
from app.models.user import UserRole, UserStatus
from app.schemas.admin import validate_password_strength
from app.services.auth_service import ADMIN_ROLES


class RegistrationRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(min_length=10, max_length=128)
    confirm_password: str = Field(min_length=10, max_length=128)
    badge_number: str = Field(min_length=2, max_length=20)
    role: UserRole
    station_id: str = Field(min_length=1, max_length=50)
    department: str = Field(min_length=1, max_length=100)
    mobile_number: str | None = Field(default=None, max_length=15, pattern=r'^\+?[0-9]{10,15}$')

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        return validate_password_strength(v)

    @field_validator("role")
    @classmethod
    def restrict_roles(cls, v):
        if v in ADMIN_ROLES:
            raise ValueError("Cannot self-register with administrative roles")
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class RegistrationResponse(BaseModel):
    message: str
    user_id: int
    email: str


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=10, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        return validate_password_strength(v)


class PendingRegistrationResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    station_id: str | None
    department: str | None
    badge_number: str | None
    mobile_number: str | None
    status: str
    email_verified: bool
    admin_approved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RegistrationStatsResponse(BaseModel):
    pending: int
    active: int
    suspended: int
    rejected: int
    total: int


class ApprovalAction(BaseModel):
    action: str = Field(pattern=r'^(approve|reject|suspend|reactivate)$')
    reason: str | None = Field(default=None, max_length=500)
