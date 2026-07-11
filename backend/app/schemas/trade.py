"""
Pydantic schemas for Trade endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TradeCreate(BaseModel):
    symbol: str = Field(examples=["R_100", "frxEURUSD"])
    contract_type: str = Field(examples=["CALL", "PUT"])
    stake: float = Field(gt=0)
    duration: int = Field(gt=0)
    duration_unit: str = Field(examples=["t", "s", "m"])
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None


class TradeResponse(BaseModel):
    id: int
    contract_id: Optional[str]
    symbol: str
    contract_type: str
    stake: float
    payout: Optional[float]
    profit: Optional[float]
    entry_price: Optional[float]
    exit_price: Optional[float]
    take_profit: Optional[float]
    stop_loss: Optional[float]
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
