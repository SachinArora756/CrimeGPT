from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.case_service import get_case_by_id

router = APIRouter()


class IntakeRequest(BaseModel):
    complaint_text: str
    language: str = "en"


class IntakeResponse(BaseModel):
    complainant_name: str | None = None
    accused_name: str | None = None
    incident_date: str | None = None
    incident_location: str | None = None
    offense_type: str | None = None
    suggested_sections: list[str] = []
    summary: str = ""


class InvestigationRequest(BaseModel):
    case_id: int
    context: str | None = None


class InvestigationResponse(BaseModel):
    recommendations: list[str]
    next_steps: list[str]
    legal_references: list[str]
    risk_assessment: str


class LegalQueryRequest(BaseModel):
    query: str
    case_id: int | None = None


class LegalQueryResponse(BaseModel):
    provisions: list[dict]
    analysis: str
    relevance_score: float


@router.post("/intake", response_model=IntakeResponse)
async def process_intake(
    request: IntakeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.ai.agents.case_intake import extract_case_data

    result = await extract_case_data(request.complaint_text, request.language)
    return IntakeResponse(**result)


@router.post("/investigate", response_model=InvestigationResponse)
async def run_investigation(
    request: InvestigationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await get_case_by_id(db, request.case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    from app.ai.agents.investigation import investigate_case

    result = await investigate_case(case, request.context)
    return InvestigationResponse(**result)


@router.post("/legal-query", response_model=LegalQueryResponse)
async def query_legal(
    request: LegalQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.ai.agents.legal_rag import query_legal_provisions

    result = await query_legal_provisions(request.query, request.case_id)
    return LegalQueryResponse(**result)


class TranscribeResponse(BaseModel):
    text: str
    language: str


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import UploadFile, File
    return TranscribeResponse(text="", language="en")
