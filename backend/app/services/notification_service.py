from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.models.user import User


async def create_notification(
    db: AsyncSession,
    user_id: int,
    type: NotificationType,
    title: str,
    message: str,
    case_id: int | None = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        case_id=case_id,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


async def notify_case_team(
    db: AsyncSession,
    case,
    type: NotificationType,
    title: str,
    message: str,
    exclude_user_id: int | None = None,
):
    user_ids = set()
    if case.assigned_officer_id:
        user_ids.add(case.assigned_officer_id)
    if case.investigation_team:
        for uid in case.investigation_team:
            user_ids.add(uid)

    if exclude_user_id:
        user_ids.discard(exclude_user_id)

    for uid in user_ids:
        notif = Notification(
            user_id=uid,
            type=type,
            title=title,
            message=message,
            case_id=case.id,
        )
        db.add(notif)
    if user_ids:
        await db.commit()


async def get_notifications(
    db: AsyncSession, user_id: int, limit: int = 50, offset: int = 0
) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_unread_count(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
    )
    return result.scalar() or 0


async def mark_read(db: AsyncSession, notification_id: int, user_id: int) -> bool:
    result = await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(is_read=True)
    )
    await db.commit()
    return result.rowcount > 0


async def mark_all_read(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return result.rowcount


async def delete_notification(db: AsyncSession, notification_id: int, user_id: int) -> bool:
    from sqlalchemy import delete as sql_delete
    result = await db.execute(
        sql_delete(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
    )
    await db.commit()
    return result.rowcount > 0


async def notify_evidence_uploaded(db: AsyncSession, case, uploader_id: int, filename: str):
    await notify_case_team(
        db, case,
        NotificationType.EVIDENCE_UPLOADED,
        "New Evidence Uploaded",
        f"File '{filename}' uploaded to case {case.fir_number}",
        exclude_user_id=uploader_id,
    )


async def notify_status_changed(db: AsyncSession, case, actor_id: int, old_status: str, new_status: str):
    await notify_case_team(
        db, case,
        NotificationType.STATUS_CHANGED,
        "Case Status Updated",
        f"Case {case.fir_number} status changed from {old_status} to {new_status}",
        exclude_user_id=actor_id,
    )


async def notify_document_generated(db: AsyncSession, case, actor_id: int, doc_type: str):
    await notify_case_team(
        db, case,
        NotificationType.DOCUMENT_GENERATED,
        "Document Generated",
        f"{doc_type.replace('_', ' ').title()} generated for case {case.fir_number}",
        exclude_user_id=actor_id,
    )


async def notify_case_assigned(db: AsyncSession, case, assigner_id: int, assignee_id: int):
    await create_notification(
        db, assignee_id,
        NotificationType.CASE_ASSIGNED,
        "Case Assigned to You",
        f"Case {case.fir_number} has been assigned to you",
        case_id=case.id,
    )
