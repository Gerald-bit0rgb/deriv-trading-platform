"""
CRUD operations for BotSession — persists bot state across server restarts.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bot_session import BotSession


async def get_bot_session(db: AsyncSession, user_id: int) -> Optional[BotSession]:
    result = await db.execute(
        select(BotSession).where(BotSession.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def save_bot_started(
    db: AsyncSession, user_id: int, symbol: str, account_type: str
) -> BotSession:
    """Mark bot as active and save the symbol/account so it can restart."""
    session = await get_bot_session(db, user_id)
    if session is None:
        session = BotSession(user_id=user_id)
        db.add(session)
    session.is_active = True
    session.symbol = symbol
    session.account_type = account_type
    session.started_at = datetime.now(timezone.utc)
    session.stopped_at = None
    await db.flush()
    return session


async def save_bot_stopped(db: AsyncSession, user_id: int) -> None:
    """Mark bot as stopped."""
    session = await get_bot_session(db, user_id)
    if session:
        session.is_active = False
        session.stopped_at = datetime.now(timezone.utc)
        await db.flush()


async def get_all_active_sessions(db: AsyncSession) -> List[BotSession]:
    """Get all users who had the bot running before the last server restart."""
    result = await db.execute(
        select(BotSession).where(BotSession.is_active == True)  # noqa: E712
    )
    return list(result.scalars().all())
