from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.case import CaseStatus
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseListResponse
from app.services.auth_service import get_current_user
from app.services.case_service import create_case, get_case_by_id, get_cases, update_case

router = APIRouter()


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_new_case(
    case_data: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await create_case(db, case_data, current_user.id)
    return CaseResponse.model_validate(case)


@router.get("/", response_model=CaseListResponse)
async def list_cases(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: CaseStatus | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cases, total = await get_cases(db, page, per_page, status, search)
    return CaseListResponse(
        cases=[CaseResponse.model_validate(c) for c in cases],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return CaseResponse.model_validate(case)


@router.put("/{case_id}", response_model=CaseResponse)
async def update_existing_case(
    case_id: int,
    case_data: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await update_case(db, case_id, case_data)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return CaseResponse.model_validate(case)
