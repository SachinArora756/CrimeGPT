from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    postgres_user: str = "crimegpt"
    postgres_password: str = "crimegpt_secret"
    postgres_db: str = "crimegpt"
    database_url: str = "postgresql+asyncpg://crimegpt:crimegpt_secret@localhost:5432/crimegpt"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    gemini_api_key: str = ""

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    upload_dir: str = "./data/uploads"

    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
