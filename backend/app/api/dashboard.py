"""
Dashboard aggregation route.

GET /api/v1/dashboard — single call that returns everything the dashboard needs.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.crud.trade import get_daily_summary, get_open_trades
from app.crud.risk import get_or_create_risk_settings
from app.models.trade import Trade
from app.models.user import User
from app.services import trading_engine

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
async def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return all data needed to render the main dashboard screen:
      - Account balance (from Deriv if session active, else None)
      - Open trades
      - Today's stats
      - All-time stats
      - Bot status
      - Risk settings summary
    """
    # ── Live balance ─────────────────────────────────────────────────────────
    balance_data = {"balance": None, "currency": None, "equity": None}
    session = trading_engine.get_session(current_user.id)
    if session and session.client:
        try:
            bal = await session.client.get_balance()
            balance_data = {
                "balance": bal.get("balance"),
                "currency": bal.get("currency"),
                "equity": bal.get("balance"),  # Deriv doesn't separate equity for binary options
            }
        except Exception:
            pass  # fail silently — bot may be connecting

    # ── Today's summary ───────────────────────────────────────────────────────
    daily = await get_daily_summary(db, current_user.id)

    # ── All-time stats ────────────────────────────────────────────────────────
    result = await db.execute(
        select(
            func.count(Trade.id).label("total"),
            func.coalesce(func.sum(Trade.profit), 0.0).label("total_profit"),
            func.sum(func.cast(Trade.is_win.is_(True), func.Integer)).label("wins"),
        ).where(Trade.user_id == current_user.id, Trade.status == "closed")
    )
    row = result.one()
    total_closed = row.total or 0
    total_wins   = row.wins or 0

    # ── Open trades ───────────────────────────────────────────────────────────
    open_trades = await get_open_trades(db, current_user.id)

    # ── Risk settings ─────────────────────────────────────────────────────────
    risk = await get_or_create_risk_settings(db, current_user.id)

    # ── 7-day equity curve (profit per day) ───────────────────────────────────
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    equity_result = await db.execute(
        select(
            func.date_trunc("day", Trade.closed_at).label("day"),
            func.coalesce(func.sum(Trade.profit), 0.0).label("day_profit"),
        )
        .where(
            Trade.user_id == current_user.id,
            Trade.status == "closed",
            Trade.closed_at >= seven_days_ago,
        )
        .group_by(func.date_trunc("day", Trade.closed_at))
        .order_by(func.date_trunc("day", Trade.closed_at))
    )
    equity_curve = [
        {"date": str(r.day)[:10], "profit": float(r.day_profit)}
        for r in equity_result.all()
    ]

    bot_status = trading_engine.get_bot_status(current_user.id)

    return {
        "account": {
            **balance_data,
            "username": current_user.username,
            "deriv_account_id": current_user.deriv_account_id,
            "has_deriv_token": bool(current_user.deriv_api_token),
        },
        "bot": {
            "status": bot_status,
        },
        "today": {
            "trades": daily["today_trades"],
            "profit": daily["today_profit"],
            "win_rate": daily["today_win_rate"],
        },
        "all_time": {
            "total_trades": total_closed,
            "total_profit": float(row.total_profit or 0),
            "win_rate": (total_wins / total_closed * 100) if total_closed > 0 else 0.0,
            "loss_rate": ((total_closed - total_wins) / total_closed * 100) if total_closed > 0 else 0.0,
        },
        "open_trades": len(open_trades),
        "equity_curve": equity_curve,
        "risk": {
            "emergency_stop": risk.emergency_stop,
            "trading_enabled": risk.trading_enabled,
            "max_daily_loss": risk.max_daily_loss,
            "daily_profit_target": risk.daily_profit_target,
            "max_open_trades": risk.max_open_trades,
        },
    }
