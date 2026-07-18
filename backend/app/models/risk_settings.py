"""
RiskSettings model — one row per user, stores all risk management parameters.
Updated for lot-based trading (like MT5 EAs), not duration-based.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class RiskSettings(Base):
    __tablename__ = "risk_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False
    )

    # ── Stake per trade (USD) ───────────────────────────────────────────────
    # NOTE: field is named "lot_size" for continuity with earlier versions,
    # but Deriv's Multiplier API has no lot concept — this value is sent
    # directly as the USD stake amount. Deriv enforces a $1.00 minimum stake.
    default_lot_size: Mapped[float] = mapped_column(Float, default=1.0)
    max_lot_size: Mapped[float] = mapped_column(Float, default=100.0)

    # ── Daily loss limit (in USD or account currency) ─────────────────────
    max_daily_loss: Mapped[float] = mapped_column(Float, default=50.0)
    max_daily_trades: Mapped[int] = mapped_column(Integer, default=100)  # unlimited for EA-style
    daily_profit_target: Mapped[float] = mapped_column(Float, default=200.0)

    # ── Risk limits (removed max_open_trades — now trade all symbols) ────
    # max_open_trades removed — bot trades all watchlist symbols
    max_drawdown_pct: Mapped[float] = mapped_column(Float, default=20.0)

    # ── Exit signals (no duration, exit on crossback) ──────────────────────
    # Trades exit when EMA crosses back through BB middle (not on duration)
    trailing_stop_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    trailing_stop_distance: Mapped[float] = mapped_column(Float, default=2.0)  # pips

    # ── Emergency controls ─────────────────────────────────────────────────
    emergency_stop: Mapped[bool] = mapped_column(Boolean, default=False)
    trading_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── AI confidence threshold ────────────────────────────────────────────
    min_ai_confidence: Mapped[float] = mapped_column(Float, default=0.65)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="risk_settings")

    def __repr__(self) -> str:
        return f"<RiskSettings user_id={self.user_id}>"
