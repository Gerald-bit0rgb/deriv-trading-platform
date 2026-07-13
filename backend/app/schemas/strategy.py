"""
Pydantic schemas for Strategy Settings endpoints.
"""
from pydantic import BaseModel, Field


class StrategySettingsUpdate(BaseModel):
    # 4H Bias
    bias_timeframe: int = Field(default=14400, description="Bias timeframe in seconds. 3600=1H, 14400=4H, 86400=1D")
    bias_fast_period: int = Field(default=5, ge=1, le=200)
    bias_slow_period: int = Field(default=13, ge=1, le=200)
    bias_ma_method: str = Field(default="EMA", description="EMA | SMA | WMA | SMMA")
    bias_applied_price: str = Field(default="CLOSE", description="CLOSE | OPEN | HIGH | LOW | MEDIAN | TYPICAL | WEIGHTED")

    # ADX filter
    adx_enabled: bool = True
    adx_period: int = Field(default=14, ge=1, le=100)
    adx_threshold: float = Field(default=20.0, ge=0, le=100)

    # 15M Entry
    entry_timeframe: int = Field(default=900, description="Entry timeframe in seconds. 60=1M, 300=5M, 900=15M, 1800=30M, 3600=1H")
    entry_fast_period: int = Field(default=5, ge=1, le=200)
    entry_fast_method: str = Field(default="EMA", description="EMA | SMA | WMA | SMMA")
    entry_slow_period: int = Field(default=50, ge=1, le=500)
    entry_slow_method: str = Field(default="SMA", description="EMA | SMA | WMA | SMMA")
    entry_applied_price: str = Field(default="TYPICAL", description="CLOSE | OPEN | HIGH | LOW | MEDIAN | TYPICAL | WEIGHTED")

    # Emergency exit
    emergency_exit_enabled: bool = True
    exit_sma_period: int = Field(default=50, ge=1, le=500)

    # Trade duration
    trade_duration: int = Field(default=5, ge=1)
    trade_duration_unit: str = Field(default="t", description="t=ticks, s=seconds, m=minutes")


class StrategySettingsResponse(StrategySettingsUpdate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
