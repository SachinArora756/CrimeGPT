import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import select, text

from app.config import settings
from app.database import engine, Base, async_session
from app.routers import auth, cases, evidence, documents, agents
from app.routers import admin, notifications, timeline, chat, dashboard, legal
from app.routers import legal_reasoning, users
from app.routers import criminal_intelligence, forensic_toolkit, ai_investigation
from app.routers import knowledge_base
from app.middleware.audit import AuditMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.utils.rate_limiter import limiter
from app.models.user import User, UserRole
from app.models.case import Case  # noqa: F401
from app.models.evidence import Evidence  # noqa: F401
from app.models.document import Document, CaseDiary, AuditLog  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.timeline import TimelineEvent  # noqa: F401
from app.models.chat import ChatMessage  # noqa: F401
from app.models.ingestion_log import IngestionLog, KBActivityLog  # noqa: F401
from app.models.legal_recommendation import LegalRecommendation  # noqa: F401
from app.models.criminal_intelligence import CriminalProfile  # noqa: F401
from app.models.forensic_toolkit import ForensicToolDefinition  # noqa: F401
from app.models.ai_investigation import AIInvestigationSession, AIInvestigationMessage  # noqa: F401
from app.models.legal_chat import LegalChatMessage  # noqa: F401
from app.services.auth_service import hash_password


_ADMIN_PASSWORD = os.environ.get("ADMIN_DEFAULT_PASSWORD", "AdminPass123!")


async def seed_admin():
    async with async_session() as db:
        result = await db.execute(select(User).where(User.role == UserRole.SUPER_ADMIN))
        if not result.scalar_one_or_none():
            admin_user = User(
                username="admin",
                email="admin@crimegpt.system",
                hashed_password=hash_password(_ADMIN_PASSWORD),
                full_name="System Administrator",
                role=UserRole.SUPER_ADMIN,
                station_id="HQ",
                department="Administration",
            )
            db.add(admin_user)
            await db.commit()


async def _ensure_schema_columns():
    """Add columns that create_all() won't add to existing tables."""
    migrations = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now()",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS account_locked BOOLEAN DEFAULT false",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS force_password_change BOOLEAN DEFAULT false",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(500)",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now()",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS public_id VARCHAR(36)",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS title VARCHAR(300)",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'medium'",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES users(id)",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS assigned_by_id INTEGER REFERENCES users(id)",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ai_confidence INTEGER",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS risk_score INTEGER",
        "ALTER TABLE evidence ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now()",
        "ALTER TABLE legal_recommendations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now()",
        "ALTER TABLE case_diary ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT now()",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_agent VARCHAR(500)",
        "ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS status_code INTEGER",
        "ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS category VARCHAR(50)",
        "ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS uploaded_by INTEGER",
        "ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1",
        "ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255)",
        "ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'",
        "ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100)",
        "ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS page_count INTEGER",
        "ALTER TABLE ingestion_logs ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'BAAI/bge-small-en-v1.5'",
    ]
    async with engine.begin() as conn:
        for stmt in migrations:
            await conn.execute(text(stmt))
        # Backfill public_id for existing cases that don't have one
        await conn.execute(text(
            "UPDATE cases SET public_id = gen_random_uuid()::text WHERE public_id IS NULL"
        ))
        # Add unique index if not exists
        await conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_cases_public_id ON cases(public_id)"
        ))


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _ensure_schema_columns()
    await seed_admin()
    await _seed_criminal_data()
    await _auto_ingest_legal_docs()
    yield
    await engine.dispose()


async def _seed_criminal_data():
    try:
        from app.seed_criminals import seed_criminal_profiles
        await seed_criminal_profiles()
    except Exception:
        pass


async def _auto_ingest_legal_docs():
    try:
        from app.ai.rag.ingestion import ingest_all_legal_documents
        await ingest_all_legal_documents(force=False)
    except Exception:
        pass


app = FastAPI(
    title="CrimeGPT API",
    description="AI-powered Investigation Operating System",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(AuditMiddleware)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(cases.router, prefix="/api/cases", tags=["Cases"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["Evidence"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(agents.router, prefix="/api/agents", tags=["AI Agents"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["Timeline"])
app.include_router(chat.router, prefix="/api/chat", tags=["AI Chat"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(legal.router, prefix="/api/legal", tags=["Legal Knowledge Base"])
app.include_router(legal_reasoning.router, prefix="/api/legal", tags=["Legal Reasoning"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(criminal_intelligence.router, prefix="/api/criminal-intelligence", tags=["Criminal Intelligence"])
app.include_router(forensic_toolkit.router, prefix="/api/forensic-toolkit", tags=["Digital Forensics Toolkit"])
app.include_router(ai_investigation.router, prefix="/api/ai-investigation", tags=["AI Investigation"])
app.include_router(knowledge_base.router, prefix="/api/knowledge-base", tags=["Knowledge Base Management"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "CrimeGPT API"}
