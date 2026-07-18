"""
Pydantic schemas for Trade endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TradeCreate(BaseModel):
    symbol: str = Field(examples=["R_100", "frxEURUSD"])
    contract_type: str = Field(examples=["MULTUP", "MULTDOWN"])
    # NOTE: named "lot_size" for continuity, but this is a direct USD stake —
    # Deriv's Multiplier API enforces a $1.00 minimum stake per trade.
    lot_size: float = Field(ge=1.0, examples=[1.0, 5.0, 10.0], description="Stake in USD (Deriv minimum: $1.00)")


class TradeResponse(BaseModel):
    id: int
    contract_id: Optional[str]
    symbol: str
    contract_type: str
    lot_size: float
    payout: Optional[float]
    profit: Optional[float]
    entry_price: Optional[float]
    exit_price: Optional[float]
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    status: str
    is_win: Optional[bool]
    ai_signal: Optional[str]
    ai_confidence: Optional[float]
    ai_reason: Optional[str]
    source: str
    opened_at: datetime
    closed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class TradeSummary(BaseModel):
    total_trades: int
    open_trades: int
    closed_trades: int
    total_profit: float
    win_rate: float
    loss_rate: float
    today_profit: float
    today_trades: int
