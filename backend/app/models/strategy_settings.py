"""
StrategySettings model — stores 1-Minute Microtrading strategy parameters per user.
Indicators: EMA 3, Bollinger Bands 18, MACD (9, 12, 26), RSI 14
Exit: Crossback (EMA crosses BB) — NO duration-based exits
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

    # ── Trend Direction Filter (e.g. 4H EMA 5/13) ───────────────────────────────
    # Gates entries: only take BUY when trend is bullish, SELL when bearish.
    # Separate from the 1M entry-confirmation indicators below.
    require_trend_alignment: Mapped[bool] = mapped_column(Boolean, default=True)
    trend_timeframe: Mapped[int] = mapped_column(Integer, default=14400)  # 4H
    trend_fast_period: Mapped[int] = mapped_column(Integer, default=5)
    trend_slow_period: Mapped[int] = mapped_column(Integer, default=13)
    trend_ma_method: Mapped[str] = mapped_column(String(10), default="EMA")
    trend_applied_price: Mapped[str] = mapped_column(String(10), default="CLOSE")

    # ── 1M Entry Confirmation ───────────────────────────────────────────────────
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

    # ── Exit signals ──────────────────────────────────────────────────────────
    # NO duration-based exits — trades exit on crossback (EMA crosses BB)
    # BUY closes when EMA crosses BELOW BB middle
    # SELL closes when EMA crosses ABOVE BB middle
    exit_on_crossback_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── ATR-based Stop Loss / Take Profit (optional, off by default) ────────────
    # Computed at entry time as entry_price ± (ATR * multiplier), then monitored
    # client-side alongside crossback/trailing-stop exits. Independent of the
    # trailing stop in Risk Settings — you can use either or both.
    use_atr_sl_tp: Mapped[bool] = mapped_column(Boolean, default=False)
    atr_period: Mapped[int] = mapped_column(Integer, default=14)
    atr_sl_multiplier: Mapped[float] = mapped_column(Float, default=1.5)
    atr_tp_multiplier: Mapped[float] = mapped_column(Float, default=2.0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="strategy_settings")

    def __repr__(self) -> str:
        return f"<StrategySettings user_id={self.user_id} strategy=1M_Microtrading_Crossback>"
