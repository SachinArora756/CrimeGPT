from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.services.auth_service import get_current_user
from app.services.notification_service import (
    get_notifications,
    get_unread_count,
    mark_read,
    mark_all_read,
    delete_notification,
)

router = APIRouter()


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifications = await get_notifications(db, current_user.id, limit, offset)
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = await get_unread_count(db, current_user.id)
    return UnreadCountResponse(count=count)


@router.put("/{notification_id}/read")
async def read_notification(
    notification_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = await mark_read(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"status": "ok"}


@router.put("/mark-all-read")
async def read_all(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = await mark_all_read(db, current_user.id)
    return {"marked": count}


@router.delete("/{notification_id}")
async def remove_notification(
    notification_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = await delete_notification(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"status": "deleted"}
