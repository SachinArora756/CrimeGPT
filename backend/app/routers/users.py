from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole, ROLE_HIERARCHY
from app.models.case import Case, CaseStatus
from app.models.evidence import Evidence
from app.models.document import Document
from app.services.auth_service import get_current_user

router = APIRouter()


def _authorize_user_access(current_user: User, target_user_id: int):
    """Only allow self-access or admin/ACP+ access to other user profiles."""
    if current_user.id == target_user_id:
        return
    if ROLE_HIERARCHY[current_user.role] >= ROLE_HIERARCHY[UserRole.ACP]:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: cannot view other users' data"
    )


@router.get("/{user_id}/profile")
async def get_user_profile(
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _authorize_user_access(current_user, user_id)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "station_id": user.station_id,
        "badge_number": user.badge_number,
        "department": user.department,
        "phone": getattr(user, 'phone', None),
        "is_active": user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _authorize_user_access(current_user, user_id)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    total_cases = (await db.execute(
        select(func.count(Case.id)).where(Case.assigned_officer_id == user_id)
    )).scalar() or 0

    active_cases = (await db.execute(
        select(func.count(Case.id)).where(
            Case.assigned_officer_id == user_id,
            Case.status.in_([CaseStatus.REGISTERED, CaseStatus.INVESTIGATING])
        )
    )).scalar() or 0

    closed_cases = (await db.execute(
        select(func.count(Case.id)).where(
            Case.assigned_officer_id == user_id,
            Case.status == CaseStatus.CLOSED
        )
    )).scalar() or 0

    high_priority = (await db.execute(
        select(func.count(Case.id)).where(
            Case.assigned_officer_id == user_id,
            Case.priority.in_(["high", "critical"])
        )
    )).scalar() or 0

    case_ids_q = select(Case.id).where(Case.assigned_officer_id == user_id)
    total_evidence = (await db.execute(
        select(func.count(Evidence.id)).where(Evidence.case_id.in_(case_ids_q))
    )).scalar() or 0

    total_documents = (await db.execute(
        select(func.count(Document.id)).where(Document.case_id.in_(case_ids_q))
    )).scalar() or 0

    cases_by_status = {}
    for s in CaseStatus:
        count = (await db.execute(
            select(func.count(Case.id)).where(
                Case.assigned_officer_id == user_id,
                Case.status == s
            )
        )).scalar() or 0
        if count > 0:
            cases_by_status[s.value] = count

    recent_q = (
        select(Case)
        .where(Case.assigned_officer_id == user_id)
        .order_by(Case.created_at.desc())
        .limit(10)
    )
    recent_result = await db.execute(recent_q)
    recent_cases = [
        {
            "id": c.id,
            "public_id": c.public_id,
            "fir_number": c.fir_number,
            "title": c.title,
            "status": c.status.value if c.status else None,
            "priority": c.priority or "medium",
            "complainant_name": c.complainant_name,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in recent_result.scalars().all()
    ]

    return {
        "total_cases": total_cases,
        "active_cases": active_cases,
        "closed_cases": closed_cases,
        "high_priority_cases": high_priority,
        "total_evidence": total_evidence,
        "total_documents": total_documents,
        "cases_by_status": cases_by_status,
        "recent_cases": recent_cases,
    }
