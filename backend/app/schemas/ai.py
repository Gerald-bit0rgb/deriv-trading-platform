"""
Pydantic schemas for AI / signal endpoints.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AISignalResponse(BaseModel):
    symbol: str
    signal: str                    # BUY | SELL | WAIT
    confidence: float              # 0.0 – 1.0
    reason: str
    trend: str                     # BULLISH | BEARISH | SIDEWAYS
    volatility: str                # HIGH | MEDIUM | LOW
    pattern: Optional[str]         # detected candlestick / technical pattern
    entry_price: Optional[float]
    suggested_stake: Optional[float]
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
