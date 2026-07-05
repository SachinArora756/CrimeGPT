from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole, ROLE_HIERARCHY
from app.models.case import Case


def can_access_case(user: User, case: Case) -> bool:
    if ROLE_HIERARCHY[user.role] >= ROLE_HIERARCHY[UserRole.ACP]:
        return True
    if case.assigned_officer_id == user.id:
        return True
    if case.investigation_team and user.id in case.investigation_team:
        return True
    if ROLE_HIERARCHY[user.role] >= ROLE_HIERARCHY[UserRole.INSPECTOR]:
        if case.station_id and case.station_id == user.station_id:
            return True
    return False


def can_modify_case(user: User, case: Case) -> bool:
    if ROLE_HIERARCHY[user.role] >= ROLE_HIERARCHY[UserRole.ACP]:
        return True
    if ROLE_HIERARCHY[user.role] >= ROLE_HIERARCHY[UserRole.SHO]:
        if case.station_id and case.station_id == user.station_id:
            return True
    if case.assigned_officer_id == user.id:
        return True
    return False


async def authorize_case_access(db: AsyncSession, case_id: str | int, user: User) -> Case:
    if isinstance(case_id, int):
        result = await db.execute(select(Case).where(Case.id == case_id))
    else:
        result = await db.execute(select(Case).where(Case.public_id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not can_access_case(user, case):
        await _log_idor_attempt(db, user, str(case_id))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this case")
    return case


async def authorize_case_modify(db: AsyncSession, case_id: str, user: User) -> Case:
    case = await authorize_case_access(db, case_id, user)
    if not can_modify_case(user, case):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to modify this case")
    return case


def filter_cases_for_user(query, user: User):
    if ROLE_HIERARCHY[user.role] >= ROLE_HIERARCHY[UserRole.ACP]:
        return query

    from sqlalchemy import cast, String
    team_contains = cast(Case.investigation_team, String).contains(f"{user.id}")

    if ROLE_HIERARCHY[user.role] >= ROLE_HIERARCHY[UserRole.INSPECTOR]:
        return query.where(
            or_(
                Case.station_id == user.station_id,
                Case.assigned_officer_id == user.id,
                team_contains,
            )
        )

    return query.where(
        or_(
            Case.assigned_officer_id == user.id,
            team_contains,
        )
    )


async def _log_idor_attempt(db: AsyncSession, user: User, case_id: str):
    try:
        from app.models.document import AuditLog
        from app.database import async_session
        from datetime import datetime
        async with async_session() as audit_db:
            log = AuditLog(
                user_id=user.id,
                action="BLOCKED_IDOR_ATTEMPT",
                resource_type="case",
                resource_id=str(case_id),
                details={"role": user.role.value, "station_id": user.station_id},
                timestamp=datetime.utcnow(),
            )
            audit_db.add(log)
            await audit_db.commit()
    except Exception:
        pass
