import secrets
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


def _generate_secret() -> str:
    return secrets.token_hex(32)


class Settings(BaseSettings):
    postgres_user: str = "crimegpt"
    postgres_password: str = "crimegpt_secret"
    postgres_db: str = "crimegpt"
    database_url: str = "postgresql+asyncpg://crimegpt:crimegpt_secret@localhost:5432/crimegpt"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    gemini_api_key: str = ""
    openrouter_api_key: str = ""

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    upload_dir: str = "./data/uploads"

    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    min_password_length: int = 10

    @field_validator("jwt_secret_key", mode="before")
    @classmethod
    def ensure_jwt_secret(cls, v: str) -> str:
        if not v or v == "your-super-secret-key-change-in-production":
            return _generate_secret()
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
