"""
CRUD operations for Notifications.
"""
from typing import List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession, user_id: int, type_: str, title: str, body: str
) -> Notification:
    notif = Notification(user_id=user_id, type=type_, title=title, body=body)
    db.add(notif)
    await db.flush()
    return notif


async def get_notifications(
    db: AsyncSession, user_id: int, unread_only: bool = False, limit: int = 50
) -> List[Notification]:
    q = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        q = q.where(Notification.is_read == False)  # noqa: E712
    q = q.order_by(Notification.sent_at.desc()).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())


async def mark_all_read(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )
