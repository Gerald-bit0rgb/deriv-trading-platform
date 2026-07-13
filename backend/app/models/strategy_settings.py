"""
StrategySettings model — stores MA Bias Basket strategy parameters per user.
All fields match the MQL5 EA inputs exactly.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class StrategySettings(Base):
    __tablename__ = "strategy_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False
    )

    # ── 4H Bias timeframe ─────────────────────────────────────────────────────
    # Timeframe in seconds: 3600=1H, 14400=4H, 86400=1D
    bias_timeframe: Mapped[int] = mapped_column(Integer, default=14400)
    bias_fast_period: Mapped[int] = mapped_column(Integer, default=5)
    bias_slow_period: Mapped[int] = mapped_column(Integer, default=13)
    # MA method: EMA | SMA | WMA | SMMA
    bias_ma_method: Mapped[str] = mapped_column(String(10), default="EMA")
    # Applied price: CLOSE | OPEN | HIGH | LOW | MEDIAN | TYPICAL | WEIGHTED
    bias_applied_price: Mapped[str] = mapped_column(String(10), default="CLOSE")

    # ── ADX filter ────────────────────────────────────────────────────────────
    adx_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    adx_period: Mapped[int] = mapped_column(Integer, default=14)
    adx_threshold: Mapped[float] = mapped_column(Float, default=20.0)

    # ── 15M Entry timeframe ───────────────────────────────────────────────────
    # Timeframe in seconds: 60=1M, 300=5M, 900=15M, 1800=30M, 3600=1H
    entry_timeframe: Mapped[int] = mapped_column(Integer, default=900)
    entry_fast_period: Mapped[int] = mapped_column(Integer, default=5)
    # MA method for fast entry MA
    entry_fast_method: Mapped[str] = mapped_column(String(10), default="EMA")
    entry_slow_period: Mapped[int] = mapped_column(Integer, default=50)
    # MA method for slow entry MA
    entry_slow_method: Mapped[str] = mapped_column(String(10), default="SMA")
    # Applied price for entry MAs
    entry_applied_price: Mapped[str] = mapped_column(String(10), default="TYPICAL")

    # ── Emergency exit ────────────────────────────────────────────────────────
    emergency_exit_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # SMA period used for emergency exit (applied to entry timeframe)
    exit_sma_period: Mapped[int] = mapped_column(Integer, default=50)

    # ── Trade duration ────────────────────────────────────────────────────────
    trade_duration: Mapped[int] = mapped_column(Integer, default=5)
    # Duration unit: t=ticks, s=seconds, m=minutes
    trade_duration_unit: Mapped[str] = mapped_column(String(5), default="t")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="strategy_settings")

    def __repr__(self) -> str:
        return f"<StrategySettings user_id={self.user_id}>"
