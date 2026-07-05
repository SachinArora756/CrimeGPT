from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.authorization import authorize_case_access
from app.utils.rate_limiter import limiter

router = APIRouter()


class IntakeRequest(BaseModel):
    complaint_text: str = Field(min_length=10, max_length=50000)
    language: str = Field(default="en", max_length=10)


class IntakeResponse(BaseModel):
    complainant_name: str | None = None
    accused_name: str | None = None
    incident_date: str | None = None
    incident_location: str | None = None
    offense_type: str | None = None
    suggested_sections: list[str] = []
    summary: str = ""


class InvestigationRequest(BaseModel):
    case_id: str = Field(min_length=1)
    context: str | None = Field(default=None, max_length=5000)


class InvestigationResponse(BaseModel):
    recommendations: list[str]
    next_steps: list[str]
    legal_references: list[str]
    risk_assessment: str


class LegalQueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    case_id: str | None = Field(default=None, min_length=1)


class LegalQueryResponse(BaseModel):
    provisions: list[dict]
    analysis: str
    relevance_score: float


@router.post("/intake", response_model=IntakeResponse)
@limiter.limit("10/minute")
async def process_intake(
    request_obj: IntakeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.ai.agents.case_intake import extract_case_data
    from app.middleware.security import sanitize_input

    sanitized = sanitize_input(request_obj.complaint_text)
    try:
        result = await extract_case_data(sanitized, request_obj.language)
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service temporarily unavailable")
    return IntakeResponse(**result)


@router.post("/investigate", response_model=InvestigationResponse)
@limiter.limit("10/minute")
async def run_investigation(
    request_obj: InvestigationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, request_obj.case_id, current_user)

    from app.ai.agents.investigation import investigate_case

    try:
        result = await investigate_case(case, request_obj.context)
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service temporarily unavailable")
    return InvestigationResponse(**result)


@router.post("/legal-query", response_model=LegalQueryResponse)
@limiter.limit("20/minute")
async def query_legal(
    request_obj: LegalQueryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if request_obj.case_id:
        await authorize_case_access(db, request_obj.case_id, current_user)

    from app.ai.agents.legal_rag import query_legal_provisions
    from app.middleware.security import sanitize_input

    sanitized = sanitize_input(request_obj.query)
    try:
        result = await query_legal_provisions(sanitized, request_obj.case_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service temporarily unavailable")
    return LegalQueryResponse(**result)


class TranscribeResponse(BaseModel):
    text: str
    language: str


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TranscribeResponse(text="", language="en")
