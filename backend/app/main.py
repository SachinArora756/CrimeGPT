from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import auth, cases, evidence, documents, agents
from app.middleware.audit import AuditMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="CrimeGPT API",
    description="AI-powered Investigation Operating System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuditMiddleware)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(cases.router, prefix="/api/cases", tags=["Cases"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["Evidence"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(agents.router, prefix="/api/agents", tags=["AI Agents"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "CrimeGPT API"}
