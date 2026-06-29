from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.models.user import UserRole


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2, max_length=100)
    role: UserRole = UserRole.CONSTABLE
    station_id: str | None = None
    badge_number: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    station_id: str | None
    badge_number: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenRefresh(BaseModel):
    refresh_token: str
