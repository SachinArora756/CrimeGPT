from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.case import CaseStatus
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseListResponse
from app.services.auth_service import get_current_user
from app.services.case_service import create_case, get_cases, update_case
from app.services.authorization import authorize_case_access, filter_cases_for_user
from app.services.timeline_service import add_event
from app.services.notification_service import notify_case_team, create_notification
from app.services.completeness_service import calculate_completeness
from app.models.timeline import TimelineEventType
from app.models.notification import NotificationType

router = APIRouter()


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_new_case(
    case_data: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await create_case(db, case_data, current_user.id)
    await add_event(
        db, case.id, TimelineEventType.CASE_CREATED,
        f"Case {case.fir_number} registered",
        f"Filed by {current_user.full_name}",
        actor_id=current_user.id,
    )
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
    cases, total = await get_cases(db, page, per_page, status, search, current_user)
    return CaseListResponse(
        cases=[CaseResponse.model_validate(c) for c in cases],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str = Path(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)
    return CaseResponse.model_validate(case)


@router.put("/{case_id}", response_model=CaseResponse)
async def update_existing_case(
    *,
    case_id: str = Path(),
    case_data: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)
    old_status = case.status
    updated = await update_case(db, case.id, case_data)

    if case_data.status and case_data.status != old_status:
        await add_event(
            db, case.id, TimelineEventType.STATUS_CHANGED,
            f"Status changed to {case_data.status.value}",
            f"Changed by {current_user.full_name}",
            actor_id=current_user.id,
            extra_data={"old_status": old_status.value, "new_status": case_data.status.value},
        )
        await notify_case_team(
            db, updated, NotificationType.STATUS_CHANGED,
            f"Case {updated.fir_number} status updated",
            f"Status changed to {case_data.status.value} by {current_user.full_name}",
            exclude_user_id=current_user.id,
        )

    return CaseResponse.model_validate(updated)


@router.get("/{case_id}/completeness")
async def get_case_completeness(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = await authorize_case_access(db, case_id, current_user)
    return await calculate_completeness(db, case.id)


@router.get("/{case_id}/closure-readiness")
async def get_case_closure_readiness(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """IEAE: Verify all investigation steps are completed before case closure."""
    from app.services.case_closure_service import verify_case_closure_readiness

    case = await authorize_case_access(db, case_id, current_user)
    return await verify_case_closure_readiness(case.id, db)


@router.get("/{case_id}/evidence-correlations")
async def get_evidence_correlations(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """IEAE: Get cross-evidence correlation report for a case."""
    from app.services.investigation_memory_service import generate_correlation_report

    case = await authorize_case_access(db, case_id, current_user)
    return await generate_correlation_report(case.id, db)
