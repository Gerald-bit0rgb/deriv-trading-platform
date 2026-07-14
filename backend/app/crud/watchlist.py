"""
CRUD operations for the Watchlist model.
"""
from typing import List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import WatchlistItem

# Default symbols added when user has no watchlist
DEFAULT_SYMBOLS = ["R_100", "R_75", "R_50"]


async def get_watchlist(db: AsyncSession, user_id: int) -> List[WatchlistItem]:
    """Return all active watchlist items for a user."""
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user_id,
            WatchlistItem.is_active == True,  # noqa: E712
        ).order_by(WatchlistItem.added_at)
    )
    return list(result.scalars().all())


async def get_watchlist_symbols(db: AsyncSession, user_id: int) -> List[str]:
    """Return just the symbol strings for a user's active watchlist."""
    items = await get_watchlist(db, user_id)
    if not items:
        return DEFAULT_SYMBOLS
    return [item.symbol for item in items]


async def add_to_watchlist(
    db: AsyncSession, user_id: int, symbol: str
) -> WatchlistItem:
    """Add a symbol to the watchlist. Reactivates if previously removed."""
    # Check if already exists (even if inactive)
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user_id,
            WatchlistItem.symbol == symbol,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.is_active = True
        await db.flush()
        return existing

    item = WatchlistItem(user_id=user_id, symbol=symbol, is_active=True)
    db.add(item)
    await db.flush()
    return item


async def remove_from_watchlist(
    db: AsyncSession, user_id: int, symbol: str
) -> bool:
    """Remove a symbol from the watchlist."""
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user_id,
            WatchlistItem.symbol == symbol,
        )
    )
    item = result.scalar_one_or_none()
    if item:
        await db.delete(item)
        await db.flush()
        return True
    return False


async def clear_watchlist(db: AsyncSession, user_id: int) -> None:
    """Remove all watchlist items for a user."""
    await db.execute(
        delete(WatchlistItem).where(WatchlistItem.user_id == user_id)
    )
    await db.flush()
