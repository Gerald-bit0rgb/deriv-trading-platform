"""
Pydantic schemas for Strategy Settings endpoints.
"""
from pydantic import BaseModel, Field


class StrategySettingsUpdate(BaseModel):
    # 4H Bias
    bias_timeframe: int = Field(default=14400)
    bias_fast_period: int = Field(default=5, ge=1, le=200)
    bias_slow_period: int = Field(default=13, ge=1, le=200)
    bias_ma_method: str = Field(default="EMA")
    bias_applied_price: str = Field(default="CLOSE")

    # ADX filter
    adx_enabled: bool = True
    adx_period: int = Field(default=14, ge=1, le=100)
    adx_threshold: float = Field(default=20.0, ge=0, le=100)

    # 15M Entry
    entry_timeframe: int = Field(default=900)
    entry_fast_period: int = Field(default=5, ge=1, le=200)
    entry_fast_method: str = Field(default="EMA")
    entry_slow_period: int = Field(default=50, ge=1, le=500)
    entry_slow_method: str = Field(default="SMA")
    entry_applied_price: str = Field(default="TYPICAL")

    # Emergency exit
    emergency_exit_enabled: bool = True
    exit_sma_period: int = Field(default=50, ge=1, le=500)

    # Trade duration
    trade_duration: int = Field(default=5, ge=1)
    trade_duration_unit: str = Field(default="t")

    # Candle confirmation
    require_candle_confirmation: bool = False

    # MA Cross Exit — close trade early when entry MAs cross against position
    ma_cross_exit_enabled: bool = Field(
        default=False,
        description="Close trade early when EMA(fast) crosses SMA(slow) against position",
    )


class StrategySettingsResponse(StrategySettingsUpdate):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
