from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.database import get_db
from app.models.user import User, UserRole
from app.models.case import Case, CaseStatus
from app.models.evidence import Evidence
from app.models.document import Document
from app.schemas.admin import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminPasswordReset,
    UserListResponse,
    UserDetailResponse,
    SystemStats,
    SystemHealth,
)
from app.services.auth_service import (
    hash_password,
    get_current_user,
    require_admin,
)
from app.config import settings
from app.services.audit_service import get_audit_logs
from app.services.notification_service import create_notification
from app.models.notification import NotificationType

router = APIRouter()


@router.post("/users", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    existing = await db.execute(
        select(User).where((User.username == user_data.username) | (User.email == user_data.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already exists")

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        station_id=user_data.station_id,
        department=user_data.department,
        badge_number=user_data.badge_number,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserDetailResponse.model_validate(user)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: UserRole | None = None,
    station_id: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if station_id:
        query = query.where(User.station_id == station_id)
    if search:
        safe_search = search.replace("%", r"\%").replace("_", r"\_")
        query = query.where(
            User.full_name.ilike(f"%{safe_search}%", escape="\\")
            | User.username.ilike(f"%{safe_search}%", escape="\\")
            | User.email.ilike(f"%{safe_search}%", escape="\\")
        )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        users=[UserDetailResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserDetailResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserDetailResponse)
async def update_user(
    *,
    user_id: int = Path(ge=1),
    user_data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return UserDetailResponse.model_validate(user)


@router.post("/users/{user_id}/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    *,
    user_id: int = Path(ge=1),
    body: AdminPasswordReset,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    from datetime import datetime
    user.hashed_password = hash_password(body.new_password)
    user.failed_login_attempts = 0
    user.account_locked = False
    user.force_password_change = True
    user.password_changed_at = datetime.utcnow()
    await db.commit()
    return {"message": "Password reset successfully"}


@router.put("/users/{user_id}/toggle-active", response_model=UserDetailResponse)
async def toggle_active(
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot disable your own account")

    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)
    return UserDetailResponse.model_validate(user)


@router.put("/users/{user_id}/unlock", response_model=UserDetailResponse)
async def unlock_account(
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.account_locked = False
    user.failed_login_attempts = 0
    await db.commit()
    await db.refresh(user)
    return UserDetailResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from sqlalchemy import update, delete as sa_delete
    from app.models.document import AuditLog, Document, CaseDiary
    from app.models.notification import Notification
    from app.models.chat import ChatMessage
    from app.models.forensic_toolkit import ForensicToolExecution, ForensicSavedResult
    from app.models.ai_investigation import AIInvestigationSession
    from app.models.legal_chat import LegalChatMessage
    from app.models.legal_recommendation import LegalRecommendation
    from app.models.criminal_intelligence import CriminalSearchLog, CriminalWatchlist, CriminalProfile
    from app.models.case import Case
    from app.models.evidence import Evidence
    from app.models.timeline import TimelineEvent

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")

    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete super admin")

    username = user.username

    await db.execute(update(AuditLog).where(AuditLog.user_id == user_id).values(user_id=None))
    await db.execute(update(TimelineEvent).where(TimelineEvent.actor_id == user_id).values(actor_id=None))
    await db.execute(sa_delete(Notification).where(Notification.user_id == user_id))
    await db.execute(sa_delete(ChatMessage).where(ChatMessage.user_id == user_id))
    await db.execute(sa_delete(ForensicSavedResult).where(ForensicSavedResult.user_id == user_id))
    await db.execute(sa_delete(ForensicToolExecution).where(ForensicToolExecution.user_id == user_id))
    await db.execute(sa_delete(AIInvestigationSession).where(AIInvestigationSession.user_id == user_id))
    await db.execute(sa_delete(LegalChatMessage).where(LegalChatMessage.user_id == user_id))
    await db.execute(sa_delete(CriminalSearchLog).where(CriminalSearchLog.user_id == user_id))
    await db.execute(sa_delete(CriminalWatchlist).where(CriminalWatchlist.added_by == user_id))
    await db.execute(update(Case).where(Case.assigned_officer_id == user_id).values(assigned_officer_id=None))
    await db.execute(update(Case).where(Case.created_by_id == user_id).values(created_by_id=None))
    await db.execute(update(Case).where(Case.assigned_by_id == user_id).values(assigned_by_id=None))
    await db.execute(update(Evidence).where(Evidence.uploaded_by == user_id).values(uploaded_by=admin.id))
    await db.execute(update(Document).where(Document.generated_by == user_id).values(generated_by=admin.id))
    await db.execute(update(CaseDiary).where(CaseDiary.officer_id == user_id).values(officer_id=admin.id))
    await db.execute(update(LegalRecommendation).where(LegalRecommendation.approved_by == user_id).values(approved_by=None))
    await db.execute(update(LegalRecommendation).where(LegalRecommendation.created_by == user_id).values(created_by=admin.id))
    await db.execute(update(CriminalProfile).where(CriminalProfile.added_by == user_id).values(added_by=admin.id))

    await db.delete(user)
    await db.commit()
    return {"message": f"User {username} permanently deleted"}


@router.get("/stats", response_model=SystemStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    active_users = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar()
    total_cases = (await db.execute(select(func.count(Case.id)))).scalar()
    total_evidence = (await db.execute(select(func.count(Evidence.id)))).scalar()
    total_documents = (await db.execute(select(func.count(Document.id)))).scalar()

    cases_by_status = {}
    for s in CaseStatus:
        count = (await db.execute(select(func.count(Case.id)).where(Case.status == s))).scalar()
        cases_by_status[s.value] = count

    return SystemStats(
        total_users=total_users,
        active_users=active_users,
        total_cases=total_cases,
        cases_by_status=cases_by_status,
        total_evidence=total_evidence,
        total_documents=total_documents,
    )


@router.get("/system-health", response_model=SystemHealth)
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    db_status = "healthy"
    try:
        await db.execute(select(func.count(User.id)))
    except Exception:
        db_status = "unhealthy"

    qdrant_status = "healthy"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"http://{settings.qdrant_host}:{settings.qdrant_port}/readyz")
            if resp.status_code != 200:
                qdrant_status = "unhealthy"
    except Exception:
        qdrant_status = "unhealthy"

    return SystemHealth(
        database=db_status,
        qdrant=qdrant_status,
        storage="healthy",
    )


@router.get("/cases")
async def admin_list_cases(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    from app.models.case import Case

    query = select(Case)
    if status_filter:
        query = query.where(Case.status == status_filter)
    if search:
        safe = search.replace("%", r"\%").replace("_", r"\_")
        query = query.where(
            Case.fir_number.ilike(f"%{safe}%", escape="\\")
            | Case.complainant_name.ilike(f"%{safe}%", escape="\\")
            | Case.title.ilike(f"%{safe}%", escape="\\")
        )
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(Case.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    cases = result.scalars().all()

    officer_ids = set()
    for c in cases:
        if c.assigned_officer_id:
            officer_ids.add(c.assigned_officer_id)
        if c.created_by_id:
            officer_ids.add(c.created_by_id)
    officers_map = {}
    if officer_ids:
        officers_result = await db.execute(select(User).where(User.id.in_(officer_ids)))
        for u in officers_result.scalars().all():
            officers_map[u.id] = {
                "id": u.id, "full_name": u.full_name,
                "role": u.role.value, "station_id": u.station_id,
                "department": u.department,
            }

    cases_data = []
    for c in cases:
        cases_data.append({
            "id": c.id,
            "public_id": c.public_id,
            "fir_number": c.fir_number,
            "title": c.title,
            "complainant_name": c.complainant_name,
            "status": c.status.value if c.status else None,
            "priority": c.priority or "medium",
            "offense_type": c.offense_type,
            "station_id": c.station_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "assigned_officer": officers_map.get(c.assigned_officer_id),
            "created_by": officers_map.get(c.created_by_id),
        })

    return {"cases": cases_data, "total": total, "page": page, "per_page": per_page}


@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user_id: int | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    logs, total = await get_audit_logs(db, page, per_page, user_id, action, resource_type)

    user_ids = {log.user_id for log in logs if log.user_id}
    users_map = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in users_result.scalars().all():
            users_map[u.id] = {"username": u.username, "full_name": u.full_name}

    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": users_map.get(log.user_id, {}).get("username") if log.user_id else None,
                "full_name": users_map.get(log.user_id, {}).get("full_name") if log.user_id else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent if hasattr(log, 'user_agent') else None,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


from pydantic import BaseModel, Field


class AdminNotificationSend(BaseModel):
    user_ids: list[int] = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=2000)
    case_id: int | None = None


class AdminNotificationBroadcast(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=2000)
    case_id: int | None = None


@router.post("/notifications/send", status_code=status.HTTP_201_CREATED)
async def send_notification(
    body: AdminNotificationSend,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    sent_count = 0
    for user_id in body.user_ids:
        user_result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
        user = user_result.scalar_one_or_none()
        if user:
            await create_notification(
                db,
                user_id=user.id,
                type=NotificationType.SYSTEM,
                title=body.title,
                message=body.message,
                case_id=body.case_id,
            )
            sent_count += 1

    return {"message": f"Notification sent to {sent_count} user(s)", "sent_count": sent_count}


@router.post("/notifications/broadcast", status_code=status.HTTP_201_CREATED)
async def broadcast_notification(
    body: AdminNotificationBroadcast,
    role: UserRole | None = Query(None),
    station_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = select(User).where(User.is_active == True)
    if role:
        query = query.where(User.role == role)
    if station_id:
        query = query.where(User.station_id == station_id)

    result = await db.execute(query)
    users = result.scalars().all()

    sent_count = 0
    for user in users:
        if user.id == admin.id:
            continue
        await create_notification(
            db,
            user_id=user.id,
            type=NotificationType.SYSTEM,
            title=body.title,
            message=body.message,
            case_id=body.case_id,
        )
        sent_count += 1

    return {"message": f"Notification broadcast to {sent_count} user(s)", "sent_count": sent_count}


# --- IEAE Admin Dashboard ---

@router.get("/ieae-stats")
async def get_ieae_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """IEAE: Get Intelligent Evidence Assurance Engine statistics."""
    from app.models.forensic_toolkit import ForensicToolExecution, ExecutionStatus

    total_stmt = select(func.count(ForensicToolExecution.id))
    total_result = await db.execute(total_stmt)
    total_investigations = total_result.scalar() or 0

    completed_stmt = (
        select(func.count(ForensicToolExecution.id))
        .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
    )
    completed_result = await db.execute(completed_stmt)
    completed_count = completed_result.scalar() or 0

    failed_stmt = (
        select(func.count(ForensicToolExecution.id))
        .where(ForensicToolExecution.status == ExecutionStatus.FAILED)
    )
    failed_result = await db.execute(failed_stmt)
    failed_count = failed_result.scalar() or 0

    avg_conf_stmt = (
        select(func.avg(ForensicToolExecution.confidence_score))
        .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
        .where(ForensicToolExecution.confidence_score.isnot(None))
    )
    avg_conf_result = await db.execute(avg_conf_stmt)
    avg_confidence = float(avg_conf_result.scalar() or 0)

    tool_stats_stmt = (
        select(
            ForensicToolExecution.tool_key,
            func.count(ForensicToolExecution.id).label("executions"),
            func.avg(ForensicToolExecution.confidence_score).label("avg_confidence"),
            func.avg(ForensicToolExecution.execution_time_ms).label("avg_time"),
        )
        .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
        .group_by(ForensicToolExecution.tool_key)
    )
    tool_stats_result = await db.execute(tool_stats_stmt)
    tool_utilization = {}
    for row in tool_stats_result.all():
        tool_utilization[row.tool_key] = {
            "executions": row.executions,
            "avg_confidence": round(float(row.avg_confidence or 0), 3),
            "avg_time_ms": round(float(row.avg_time or 0), 0),
        }

    failed_tools_stmt = (
        select(
            ForensicToolExecution.tool_key,
            func.count(ForensicToolExecution.id).label("fail_count"),
        )
        .where(ForensicToolExecution.status == ExecutionStatus.FAILED)
        .group_by(ForensicToolExecution.tool_key)
        .order_by(func.count(ForensicToolExecution.id).desc())
        .limit(10)
    )
    failed_tools_result = await db.execute(failed_tools_stmt)
    skipped_analyses = [
        {"tool": row.tool_key, "count": row.fail_count, "reason": "Execution failed"}
        for row in failed_tools_result.all()
    ]

    success_rate = (completed_count / max(total_investigations, 1)) * 100
    overall_completeness = success_rate * (avg_confidence if avg_confidence else 0.7)

    return {
        "average_completeness": round(min(overall_completeness, 100.0), 1),
        "total_investigations": total_investigations,
        "total_completed": completed_count,
        "total_failed": failed_count,
        "skipped_analyses": skipped_analyses,
        "manual_reviews_pending": failed_count,
        "evidence_quality_avg": round(avg_confidence * 100, 1),
        "common_missing_analyses": skipped_analyses[:5],
        "tool_utilization": tool_utilization,
        "success_rate": round(success_rate, 1),
    }


@router.get("/iidse-stats")
async def get_iidse_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """IIDSE: Get Investigation Intelligence & Decision Support Engine statistics."""
    from app.models.forensic_toolkit import ForensicToolExecution, ExecutionStatus
    from app.models.investigation_memory import InvestigationMemory, EvidenceCorrelation
    from app.models.ai_investigation import AIInvestigationSession, AIInvestigationMessage

    memory_count_stmt = select(func.count(InvestigationMemory.id))
    memory_result = await db.execute(memory_count_stmt)
    total_memory_entries = memory_result.scalar() or 0

    correlation_count_stmt = select(func.count(EvidenceCorrelation.id))
    corr_result = await db.execute(correlation_count_stmt)
    total_correlations = corr_result.scalar() or 0

    high_conf_corr_stmt = (
        select(func.count(EvidenceCorrelation.id))
        .where(EvidenceCorrelation.confidence >= 0.8)
    )
    high_corr_result = await db.execute(high_conf_corr_stmt)
    high_confidence_correlations = high_corr_result.scalar() or 0

    session_count_stmt = select(func.count(AIInvestigationSession.id))
    session_result = await db.execute(session_count_stmt)
    total_chat_sessions = session_result.scalar() or 0

    message_count_stmt = select(func.count(AIInvestigationMessage.id))
    msg_result = await db.execute(message_count_stmt)
    total_chat_messages = msg_result.scalar() or 0

    memory_by_type_stmt = (
        select(
            InvestigationMemory.finding_type,
            func.count(InvestigationMemory.id).label("count"),
        )
        .group_by(InvestigationMemory.finding_type)
    )
    type_result = await db.execute(memory_by_type_stmt)
    memory_by_type = {row.finding_type: row.count for row in type_result.all()}

    corr_by_type_stmt = (
        select(
            EvidenceCorrelation.correlation_type,
            func.count(EvidenceCorrelation.id).label("count"),
            func.avg(EvidenceCorrelation.confidence).label("avg_confidence"),
        )
        .group_by(EvidenceCorrelation.correlation_type)
    )
    corr_type_result = await db.execute(corr_by_type_stmt)
    correlations_by_type = {
        row.correlation_type: {
            "count": row.count,
            "avg_confidence": round(float(row.avg_confidence or 0), 3),
        }
        for row in corr_type_result.all()
    }

    cases_with_memory_stmt = (
        select(func.count(func.distinct(InvestigationMemory.case_id)))
    )
    cases_mem_result = await db.execute(cases_with_memory_stmt)
    cases_with_memory = cases_mem_result.scalar() or 0

    cases_with_correlations_stmt = (
        select(func.count(func.distinct(EvidenceCorrelation.case_id)))
    )
    cases_corr_result = await db.execute(cases_with_correlations_stmt)
    cases_with_correlations = cases_corr_result.scalar() or 0

    avg_messages_stmt = (
        select(func.avg(func.count(AIInvestigationMessage.id)))
        .group_by(AIInvestigationMessage.session_id)
    )
    try:
        avg_msg_subq = (
            select(func.count(AIInvestigationMessage.id).label("msg_count"))
            .group_by(AIInvestigationMessage.session_id)
            .subquery()
        )
        avg_msgs_result = await db.execute(select(func.avg(avg_msg_subq.c.msg_count)))
        avg_messages_per_session = float(avg_msgs_result.scalar() or 0)
    except Exception:
        avg_messages_per_session = (total_chat_messages / max(total_chat_sessions, 1))

    return {
        "investigation_memory": {
            "total_entries": total_memory_entries,
            "by_type": memory_by_type,
            "cases_with_memory": cases_with_memory,
        },
        "correlations": {
            "total": total_correlations,
            "high_confidence": high_confidence_correlations,
            "by_type": correlations_by_type,
            "cases_with_correlations": cases_with_correlations,
        },
        "detective_chat": {
            "total_sessions": total_chat_sessions,
            "total_messages": total_chat_messages,
            "avg_messages_per_session": round(avg_messages_per_session, 1),
        },
        "decision_support": {
            "hypotheses_available": cases_with_memory > 0,
            "contradiction_detection_active": True,
            "timeline_reconstruction_active": True,
            "relationship_graph_active": True,
            "executive_summary_active": True,
        },
    }
