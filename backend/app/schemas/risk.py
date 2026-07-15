"""
Pydantic schemas for Risk Settings endpoints.
Updated for lot-based trading (EA-style, not duration-based).
"""
from pydantic import BaseModel, Field


class RiskSettingsUpdate(BaseModel):
    # ── Lot-based trading (not USD stake) ──────────────────────────────────
    default_lot_size: float = Field(gt=0, default=0.01, description="Lot size e.g. 0.01, 0.1, 1.0")
    max_lot_size: float = Field(gt=0, default=1.0, description="Max lot size per trade")

    # ── Daily loss limit ──────────────────────────────────────────────────
    max_daily_loss: float = Field(ge=0, default=50.0, description="Max daily loss in USD")
    max_daily_trades: int = Field(ge=1, default=100, description="Max trades per day")
    daily_profit_target: float = Field(ge=0, default=200.0, description="Daily profit target (optional)")

    # ── Risk limits ───────────────────────────────────────────────────────
    # max_open_trades removed — bot trades all watchlist symbols
    max_drawdown_pct: float = Field(ge=0, le=100, default=20.0, description="Max drawdown %")

    # ── Exit signals (no duration, exit on crossback) ──────────────────────
    trailing_stop_enabled: bool = Field(default=True)
    trailing_stop_distance: float = Field(gt=0, default=2.0, description="Trailing stop distance in pips")

    # ── Emergency controls ────────────────────────────────────────────────
    emergency_stop: bool = False
    trading_enabled: bool = True

    # ── AI confidence threshold ───────────────────────────────────────────
    min_ai_confidence: float = Field(ge=0, le=1, default=0.65)


class RiskSettingsResponse(RiskSettingsUpdate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
