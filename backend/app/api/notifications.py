"""
Notification routes.

GET   /api/v1/notifications           — list notifications (paginated)
POST  /api/v1/notifications/read-all  — mark all as read
DELETE /api/v1/notifications/{id}     — delete a single notification
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.crud.notification import get_notifications, mark_all_read
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    body: str
    is_read: bool
    sent_at: str

    model_config = {"from_attributes": True}


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the user's notification history."""
    notifs = await get_notifications(db, current_user.id, unread_only=unread_only, limit=limit)
    return [
        NotificationResponse(
            id=n.id,
            type=n.type,
            title=n.title,
            body=n.body,
            is_read=n.is_read,
            sent_at=n.sent_at.isoformat(),
        )
        for n in notifs
    ]


@router.post("/read-all")
async def read_all_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all unread notifications as read."""
    await mark_all_read(db, current_user.id)
    return {"message": "All notifications marked as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific notification."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Notification not found")
    await db.delete(notif)
    return {"message": "Notification deleted"}
