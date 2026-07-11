"""
Pydantic schemas for Risk Settings endpoints.
"""
from pydantic import BaseModel, Field


class RiskSettingsUpdate(BaseModel):
    default_stake: float = Field(gt=0, default=1.0)
    max_stake: float = Field(gt=0, default=10.0)
    max_daily_loss: float = Field(ge=0, default=50.0)
    max_daily_trades: int = Field(ge=1, default=20)
    daily_profit_target: float = Field(ge=0, default=100.0)
    max_open_trades: int = Field(ge=1, default=3)
    take_profit_pct: float = Field(ge=0, le=1, default=0.85)
    stop_loss_pct: float = Field(ge=0, le=1, default=1.0)
    trailing_stop_enabled: bool = False
    trailing_stop_pct: float = Field(ge=0, le=1, default=0.1)
    max_drawdown_pct: float = Field(ge=0, le=100, default=20.0)
    emergency_stop: bool = False
    trading_enabled: bool = True
    min_ai_confidence: float = Field(ge=0, le=1, default=0.65)


class RiskSettingsResponse(RiskSettingsUpdate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
