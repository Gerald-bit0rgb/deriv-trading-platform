"""
CRUD operations for the Trade model.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trade import Trade


async def create_trade(db: AsyncSession, **kwargs) -> Trade:
    trade = Trade(**kwargs)
    db.add(trade)
    await db.flush()
    return trade


async def get_trade_by_id(db: AsyncSession, trade_id: int, user_id: int) -> Optional[Trade]:
    result = await db.execute(
        select(Trade).where(Trade.id == trade_id, Trade.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_open_trades(db: AsyncSession, user_id: int) -> List[Trade]:
    result = await db.execute(
        select(Trade).where(Trade.user_id == user_id, Trade.status == "open")
    )
    return list(result.scalars().all())


async def get_trade_history(
    db: AsyncSession, user_id: int, limit: int = 50, offset: int = 0
) -> List[Trade]:
    result = await db.execute(
        select(Trade)
        .where(Trade.user_id == user_id)
        .order_by(Trade.opened_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def close_trade(
    db: AsyncSession,
    trade: Trade,
    exit_price: float,
    profit: float,
    payout: float,
) -> Trade:
    """Mark a trade as closed with final financial values."""
    trade.status = "closed"
    trade.exit_price = exit_price
    trade.profit = profit
    trade.payout = payout
    trade.is_win = profit > 0
    trade.closed_at = datetime.now(timezone.utc)
    await db.flush()
    return trade


async def get_daily_summary(db: AsyncSession, user_id: int) -> dict:
    """Return today's trade statistics for a user."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's closed trades
    result = await db.execute(
        select(
            func.count(Trade.id).label("count"),
            func.coalesce(func.sum(Trade.profit), 0).label("profit"),
            func.sum(
                func.cast(Trade.is_win == True, Integer)  # noqa: E712
            ).label("wins"),
        ).where(
            Trade.user_id == user_id,
            Trade.status == "closed",
            Trade.closed_at >= today_start,
        )
    )
    row = result.one()
    total = row.count or 0
    wins = row.wins or 0
    return {
        "today_trades": total,
        "today_profit": float(row.profit or 0),
        "today_win_rate": (wins / total * 100) if total > 0 else 0.0,
    }
