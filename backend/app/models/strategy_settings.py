"""
StrategySettings model — stores 1-Minute Microtrading strategy parameters per user.
Indicators: EMA 3, Bollinger Bands 18, MACD (9, 12, 26), RSI 14
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

    # ── 1M Microtrading Strategy ───────────────────────────────────────────────
    # Entry timeframe: 60=1M (hardcoded)
    entry_timeframe: Mapped[int] = mapped_column(Integer, default=60)

    # ── EMA 3 (fast entry signal) ──────────────────────────────────────────────
    ema_fast_period: Mapped[int] = mapped_column(Integer, default=3)
    ema_applied_price: Mapped[str] = mapped_column(String(10), default="CLOSE")

    # ── Bollinger Bands 18 (signal line) ───────────────────────────────────────
    bb_period: Mapped[int] = mapped_column(Integer, default=18)
    bb_std_dev: Mapped[float] = mapped_column(Float, default=2.0)
    # BB method: SMA | EMA
    bb_method: Mapped[str] = mapped_column(String(10), default="SMA")

    # ── MACD Histogram (9, 12, 26) ────────────────────────────────────────────
    macd_fast: Mapped[int] = mapped_column(Integer, default=12)
    macd_slow: Mapped[int] = mapped_column(Integer, default=26)
    macd_signal: Mapped[int] = mapped_column(Integer, default=9)

    # ── RSI 14 ───────────────────────────────────────────────────────────────
    rsi_period: Mapped[int] = mapped_column(Integer, default=14)
    rsi_overbought: Mapped[float] = mapped_column(Float, default=70.0)
    rsi_oversold: Mapped[float] = mapped_column(Float, default=30.0)

    # ── Trade duration ────────────────────────────────────────────────────────
    # For 1M scalping: typically 1-5 minutes (ticks or minutes)
    trade_duration: Mapped[int] = mapped_column(Integer, default=2)
    trade_duration_unit: Mapped[str] = mapped_column(String(5), default="m")

    # ── Risk management ───────────────────────────────────────────────────────
    # Trailing stop (pips or %) or hard TP disabled for scalping
    trailing_stop_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    trailing_stop_distance: Mapped[float] = mapped_column(Float, default=2.0)  # pips

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="strategy_settings")

    def __repr__(self) -> str:
        return f"<StrategySettings user_id={self.user_id} strategy=1M_Microtrading>"
