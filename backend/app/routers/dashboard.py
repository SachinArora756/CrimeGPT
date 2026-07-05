from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, cast, Date, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole, ROLE_HIERARCHY
from app.models.case import Case, CaseStatus
from app.models.evidence import Evidence
from app.models.document import Document, AuditLog
from app.services.auth_service import get_current_user
from app.services.authorization import filter_cases_for_user

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case_query = select(Case)
    case_query = filter_cases_for_user(case_query, current_user)

    total_result = await db.execute(
        select(func.count()).select_from(case_query.subquery())
    )
    total_cases = total_result.scalar() or 0

    active_result = await db.execute(
        select(func.count()).select_from(
            case_query.where(Case.status.in_([
                CaseStatus.REGISTERED, CaseStatus.INVESTIGATING
            ])).subquery()
        )
    )
    active_cases = active_result.scalar() or 0

    closed_result = await db.execute(
        select(func.count()).select_from(
            case_query.where(Case.status == CaseStatus.CLOSED).subquery()
        )
    )
    closed_cases = closed_result.scalar() or 0

    chargesheet_result = await db.execute(
        select(func.count()).select_from(
            case_query.where(Case.status == CaseStatus.CHARGESHEET_FILED).subquery()
        )
    )
    chargesheet_cases = chargesheet_result.scalar() or 0

    # Evidence and documents filtered to only cases user can access
    user_case_ids_q = select(Case.id)
    user_case_ids_q = filter_cases_for_user(user_case_ids_q, current_user)
    user_case_ids_result = await db.execute(user_case_ids_q)
    user_case_ids = [row[0] for row in user_case_ids_result.all()]

    if user_case_ids:
        evidence_result = await db.execute(
            select(func.count(Evidence.id)).where(Evidence.case_id.in_(user_case_ids))
        )
        total_evidence = evidence_result.scalar() or 0

        documents_result = await db.execute(
            select(func.count(Document.id)).where(Document.case_id.in_(user_case_ids))
        )
        total_documents = documents_result.scalar() or 0
    else:
        total_evidence = 0
        total_documents = 0

    status_counts = {}
    for s in CaseStatus:
        r = await db.execute(
            select(func.count()).select_from(
                case_query.where(Case.status == s).subquery()
            )
        )
        count = r.scalar() or 0
        if count > 0:
            status_counts[s.value] = count

    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_cases = await db.execute(
        select(func.count()).select_from(
            case_query.where(Case.created_at >= today_start).subquery()
        )
    )
    today_activity = today_cases.scalar() or 0

    if user_case_ids:
        today_evidence = await db.execute(
            select(func.count(Evidence.id)).where(
                Evidence.created_at >= today_start,
                Evidence.case_id.in_(user_case_ids)
            )
        )
        today_evidence_count = today_evidence.scalar() or 0

        today_docs = await db.execute(
            select(func.count(Document.id)).where(
                Document.generated_at >= today_start,
                Document.case_id.in_(user_case_ids)
            )
        )
        today_docs_count = today_docs.scalar() or 0
    else:
        today_evidence_count = 0
        today_docs_count = 0

    # Cases per day (last 30 days) — filtered to user's cases
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    cpd_query = select(
        cast(Case.created_at, Date).label("day"),
        func.count(Case.id).label("count")
    ).where(Case.created_at >= thirty_days_ago)
    cpd_query = filter_cases_for_user(cpd_query, current_user)
    cpd_query = cpd_query.group_by(cast(Case.created_at, Date)).order_by(cast(Case.created_at, Date))
    cases_per_day_result = await db.execute(cpd_query)
    cases_per_day = [{"date": str(row.day), "count": row.count} for row in cases_per_day_result.all()]

    # Crime category distribution — filtered to user's cases
    cat_query = select(
        Case.offense_type,
        func.count(Case.id).label("count")
    ).where(Case.offense_type.isnot(None))
    cat_query = filter_cases_for_user(cat_query, current_user)
    cat_query = cat_query.group_by(Case.offense_type).order_by(func.count(Case.id).desc()).limit(10)
    category_result = await db.execute(cat_query)
    crime_categories = [{"category": row.offense_type or "Unknown", "count": row.count} for row in category_result.all()]

    # Officer workload — only visible to ACP+ (admins), else empty
    officer_workload = []
    if ROLE_HIERARCHY[current_user.role] >= ROLE_HIERARCHY[UserRole.ACP]:
        workload_result = await db.execute(
            select(
                User.full_name,
                User.role,
                func.count(Case.id).label("case_count")
            ).join(Case, Case.assigned_officer_id == User.id)
            .group_by(User.id, User.full_name, User.role)
            .order_by(func.count(Case.id).desc())
            .limit(10)
        )
        officer_workload = [
            {"name": row.full_name, "role": row.role.value if row.role else "", "cases": row.case_count}
            for row in workload_result.all()
        ]

    # Case completion trend (last 30 days — closed cases by date) — filtered
    comp_query = select(
        cast(Case.updated_at, Date).label("day"),
        func.count(Case.id).label("count")
    ).where(
        and_(
            Case.status == CaseStatus.CLOSED,
            Case.updated_at >= thirty_days_ago
        )
    )
    comp_query = filter_cases_for_user(comp_query, current_user)
    comp_query = comp_query.group_by(cast(Case.updated_at, Date)).order_by(cast(Case.updated_at, Date))
    completion_result = await db.execute(comp_query)
    completion_trend = [{"date": str(row.day), "count": row.count} for row in completion_result.all()]

    # Recent activity (last 10 audit log entries for this user or all for admins)
    if ROLE_HIERARCHY[current_user.role] >= ROLE_HIERARCHY[UserRole.ACP]:
        recent_logs = await db.execute(
            select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10)
        )
    else:
        recent_logs = await db.execute(
            select(AuditLog).where(AuditLog.user_id == current_user.id)
            .order_by(AuditLog.timestamp.desc()).limit(10)
        )
    recent_activity = [
        {
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        }
        for log in recent_logs.scalars().all()
    ]

    return {
        "total_cases": total_cases,
        "active_cases": active_cases,
        "closed_cases": closed_cases,
        "chargesheet_cases": chargesheet_cases,
        "total_evidence": total_evidence,
        "total_documents": total_documents,
        "cases_by_status": status_counts,
        "today_activity": today_activity + today_evidence_count + today_docs_count,
        "today_new_cases": today_activity,
        "today_evidence": today_evidence_count,
        "today_documents": today_docs_count,
        "cases_per_day": cases_per_day,
        "crime_categories": crime_categories,
        "officer_workload": officer_workload,
        "completion_trend": completion_trend,
        "recent_activity": recent_activity,
    }


@router.get("/search")
async def global_search(
    q: str = Query(min_length=2, max_length=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    safe_q = q.replace("%", r"\%").replace("_", r"\_")
    pattern = f"%{safe_q}%"

    # Search cases
    case_query = select(Case).where(
        Case.fir_number.ilike(pattern, escape="\\")
        | Case.complainant_name.ilike(pattern, escape="\\")
        | Case.accused_name.ilike(pattern, escape="\\")
        | Case.description.ilike(pattern, escape="\\")
        | Case.offense_type.ilike(pattern, escape="\\")
        | Case.incident_location.ilike(pattern, escape="\\")
    )
    case_query = filter_cases_for_user(case_query, current_user)
    case_results = await db.execute(case_query.limit(10))
    cases = [
        {
            "type": "case",
            "id": c.public_id,
            "title": f"{c.fir_number} — {c.complainant_name}",
            "subtitle": c.offense_type or c.status.value,
            "status": c.status.value,
        }
        for c in case_results.scalars().all()
    ]

    # Search users (for admin/SHO+)
    users = []
    if ROLE_HIERARCHY[current_user.role] >= ROLE_HIERARCHY[UserRole.SHO]:
        user_results = await db.execute(
            select(User).where(
                User.full_name.ilike(pattern, escape="\\")
                | User.username.ilike(pattern, escape="\\")
                | User.badge_number.ilike(pattern, escape="\\")
            ).limit(10)
        )
        users = [
            {
                "type": "officer",
                "id": u.id,
                "title": u.full_name,
                "subtitle": f"{u.role.value.replace('_', ' ').title()} — {u.station_id or 'No station'}",
                "status": "active" if u.is_active else "inactive",
            }
            for u in user_results.scalars().all()
        ]

    # Search evidence — only from user-accessible cases
    accessible_case_ids_q = select(Case.id)
    accessible_case_ids_q = filter_cases_for_user(accessible_case_ids_q, current_user)
    accessible_ids_result = await db.execute(accessible_case_ids_q)
    accessible_ids = [row[0] for row in accessible_ids_result.all()]

    if accessible_ids:
        evidence_results = await db.execute(
            select(Evidence).where(
                Evidence.case_id.in_(accessible_ids),
                (
                    Evidence.original_filename.ilike(pattern, escape="\\")
                    | Evidence.ocr_text.ilike(pattern, escape="\\")
                    | Evidence.description.ilike(pattern, escape="\\")
                )
            ).limit(10)
        )
        evidence = [
            {
                "type": "evidence",
                "id": e.id,
                "title": e.original_filename,
                "subtitle": e.file_type,
                "case_id": e.case_id,
            }
            for e in evidence_results.scalars().all()
        ]
    else:
        evidence = []

    return {
        "cases": cases,
        "officers": users,
        "evidence": evidence,
        "total": len(cases) + len(users) + len(evidence),
    }
