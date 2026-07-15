"""
Pydantic schemas for AI / signal endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AISignalResponse(BaseModel):
    symbol: str
    signal: str                        # BUY | SELL | WAIT
    confidence: float                  # 0.0 – 1.0
    reason: str
    ema3_value: Optional[float] = None
    bb_middle: Optional[float] = None
    macd_histogram: Optional[float] = None
    rsi_value: Optional[float] = None
    volatility: str = "MEDIUM"         # HIGH | MEDIUM | LOW
    trend_direction: Optional[str] = None   # BULLISH | BEARISH | NEUTRAL
    generated_at: datetime


class MarketAnalysis(BaseModel):
    symbol: str
    current_price: float
    price_change_24h: float
    price_change_pct: float
    high_24h: float
    low_24h: float
    volatility_score: float
    trend_strength: float          # 0–100 (ADX value)
    support_levels: list[float]
    resistance_levels: list[float]
    indicators: dict               # RSI, MACD, BB, etc.
    analysed_at: datetime
