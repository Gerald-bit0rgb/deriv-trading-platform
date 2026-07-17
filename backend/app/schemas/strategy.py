"""
Pydantic schemas for 1-Minute Microtrading Strategy Settings endpoints.
Exit: Crossback only (no duration) — EA-style trading.
"""
from pydantic import BaseModel, Field


class StrategySettingsUpdate(BaseModel):
    # ── Trend Direction Filter (e.g. 4H EMA 5/13) ───────────────────────────────
    # Gates entries: only BUY when trend is bullish, only SELL when bearish.
    require_trend_alignment: bool = Field(default=True, description="Require 4H trend to align with 1M entry")
    trend_timeframe: int = Field(default=14400, description="Trend timeframe in seconds — 14400 = 4H")
    trend_fast_period: int = Field(default=5, ge=1, le=200)
    trend_slow_period: int = Field(default=13, ge=1, le=200)
    trend_ma_method: str = Field(default="EMA", description="EMA, SMA, WMA, or SMMA")
    trend_applied_price: str = Field(default="CLOSE")

    # ── Entry Timeframe ────────────────────────────────────────────────────────
    # Configurable — defaults to 1 minute (60s) for the microtrading strategy,
    # but can be changed the same way as the trend timeframe.
    entry_timeframe: int = Field(default=60, description="Entry candle timeframe in seconds")

    # ── EMA 3 (fast entry signal) ─────────────────────────────────────────────
    ema_fast_period: int = Field(default=3, ge=1, le=50)
    ema_applied_price: str = Field(default="CLOSE")

    # ── Bollinger Bands 18 ────────────────────────────────────────────────────
    bb_period: int = Field(default=18, ge=5, le=100)
    bb_std_dev: float = Field(default=2.0, ge=0.5, le=5.0)
    bb_method: str = Field(default="SMA", description="SMA or EMA")

    # ── MACD Histogram (9, 12, 26) ────────────────────────────────────────────
    macd_fast: int = Field(default=12, ge=5, le=50)
    macd_slow: int = Field(default=26, ge=10, le=100)
    macd_signal: int = Field(default=9, ge=2, le=50)

    # ── RSI 14 ────────────────────────────────────────────────────────────────
    rsi_period: int = Field(default=14, ge=2, le=50)
    rsi_overbought: float = Field(default=70.0, ge=50, le=100)
    rsi_oversold: float = Field(default=30.0, ge=0, le=50)

    # ── Exit signals ──────────────────────────────────────────────────────────
    # NO duration fields — exit on crossback (EMA crosses BB) only
    exit_on_crossback_enabled: bool = Field(default=True, description="Exit when EMA crosses back through BB middle")

    # ── ATR-based Stop Loss / Take Profit (optional, off by default) ────────────
    # Independent of the trailing stop in Risk Settings — you can use either or both.
    use_atr_sl_tp: bool = Field(default=False, description="Enable ATR-based stop-loss/take-profit")
    atr_period: int = Field(default=14, ge=2, le=100)
    atr_sl_multiplier: float = Field(default=1.5, ge=0.1, le=10.0, description="Stop-loss distance = ATR × this")
    atr_tp_multiplier: float = Field(default=2.0, ge=0.1, le=10.0, description="Take-profit distance = ATR × this")


class StrategySettingsResponse(StrategySettingsUpdate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
