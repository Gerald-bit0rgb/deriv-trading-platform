"""
Risk Manager — evaluates whether a proposed trade is safe to execute.

Called by the trading engine and AI engine before every trade.
Returns a RiskCheckResult describing pass/fail and the reason.
"""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud.risk import get_or_create_risk_settings
from app.crud.trade import get_daily_summary
from app.models.risk_settings import RiskSettings

logger = get_logger(__name__)


@dataclass
class RiskCheckResult:
    allowed: bool
    reason: str
    adjusted_lot_size: Optional[float] = None   # engine may reduce lot size


async def check_trade_allowed(
    db: AsyncSession,
    user_id: int,
    requested_lot_size: float,
    symbol: str,
    current_balance: float,
) -> RiskCheckResult:
    """
    Run all risk checks for a proposed trade.

    Returns RiskCheckResult(allowed=False, reason=...) if any check fails.
    """
    settings: RiskSettings = await get_or_create_risk_settings(db, user_id)

    # ── Emergency stop ────────────────────────────────────────────────────────
    if settings.emergency_stop:
        return RiskCheckResult(False, "Emergency stop is active")

    if not settings.trading_enabled:
        return RiskCheckResult(False, "Trading is disabled in risk settings")

    # ── Lot size limits ─────────────────────────────────────────────────────
    lot_size = requested_lot_size
    if lot_size > settings.max_lot_size:
        logger.warning("risk.lot_size_exceeded", requested=lot_size, max=settings.max_lot_size)
        # Automatically reduce lot size to max instead of rejecting
        lot_size = settings.max_lot_size

    if lot_size < settings.default_lot_size:
        lot_size = settings.default_lot_size

    # ── Drawdown check ────────────────────────────────────────────────────────
    if current_balance > 0:
        # We don't know the starting balance, so use a proxy: if the stake
        # would push potential loss over max_drawdown_pct of current balance
        max_loss_from_balance = current_balance * (settings.max_drawdown_pct / 100)
        summary = await get_daily_summary(db, user_id)
        realised_loss = abs(min(summary["today_profit"], 0))
        if realised_loss >= max_loss_from_balance:
            return RiskCheckResult(
                False,
                f"Max drawdown {settings.max_drawdown_pct}% reached "
                f"(lost {realised_loss:.2f} of {max_loss_from_balance:.2f})",
            )

    # ── Daily loss limit ──────────────────────────────────────────────────────
    summary = await get_daily_summary(db, user_id)
    if summary["today_profit"] <= -abs(settings.max_daily_loss):
        return RiskCheckResult(
            False,
            f"Daily loss limit of {settings.max_daily_loss} reached",
        )

    # ── Daily profit target (optional — stop after hitting target) ────────────
    if summary["today_profit"] >= settings.daily_profit_target:
        return RiskCheckResult(
            False,
            f"Daily profit target of {settings.daily_profit_target} reached — well done!",
        )

    # ── Daily trade count ─────────────────────────────────────────────────────
    if summary["today_trades"] >= settings.max_daily_trades:
        return RiskCheckResult(
            False,
            f"Daily trade limit of {settings.max_daily_trades} reached",
        )

    logger.info(
        "risk.check_passed",
        user_id=user_id,
        symbol=symbol,
        lot_size=lot_size,
    )
    return RiskCheckResult(True, "All risk checks passed", adjusted_lot_size=lot_size)


def calculate_lot_size(
    balance: float,
    risk_pct: float = 1.0,
    min_lot: float = 0.01,
    max_lot: float = 1.0,
) -> float:
    """
    Kelly-inspired position sizing, in lots rather than a USD stake.

    Risk *risk_pct* percent of balance per trade, clamped between min and max.
    """
    lot_size = balance * (risk_pct / 100) / 100  # rough $100-per-lot scaling
    return max(min_lot, min(lot_size, max_lot))


def trailing_stop_price(
    entry_price: float,
    current_price: float,
    direction: str,
    trail_pct: float = 0.05,
) -> float:
    """
    Calculate the current trailing-stop trigger price.

    :param direction: "BUY"/"MULTUP" (price must stay above) or "SELL"/"MULTDOWN" (price must stay below)
    :param trail_pct: how far below/above the peak the stop sits (as a fraction)
    """
    if direction in ("BUY", "MULTUP"):
        # Stop rises with price; trails below the peak
        return current_price * (1 - trail_pct)
    else:
        # Stop falls with price; trails above the trough
        return current_price * (1 + trail_pct)
