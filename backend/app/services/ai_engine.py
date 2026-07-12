"""
AI Trading Signal Engine.

Architecture (designed to be upgraded to a trained ML model later):

  1. Fetch recent candle data from Deriv
  2. Compute technical indicators (RSI, MACD, Bollinger Bands, EMA, ATR, ADX)
  3. Detect candlestick/chart patterns
  4. Combine signals using a weighted rule-based decision engine
  5. Output: BUY | SELL | WAIT  with a confidence score and human-readable reason

The engine is intentionally modular so each step can be replaced with a
trained scikit-learn / TensorFlow model without changing the external API.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.core.logging import get_logger
from app.services.deriv_client import DerivClient

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Signal:
    symbol: str
    signal: str                       # BUY | SELL | WAIT
    confidence: float                 # 0.0 – 1.0
    reason: str
    trend: str                        # BULLISH | BEARISH | SIDEWAYS
    volatility: str                   # HIGH | MEDIUM | LOW
    pattern: Optional[str] = None
    entry_price: Optional[float] = None
    suggested_stake: Optional[float] = None
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ─────────────────────────────────────────────────────────────────────────────
# Technical indicators (pure NumPy — no pandas required for small arrays)
# ─────────────────────────────────────────────────────────────────────────────

def _ema(prices: np.ndarray, period: int) -> np.ndarray:
    """Exponential Moving Average."""
    k = 2 / (period + 1)
    ema = np.zeros_like(prices)
    ema[0] = prices[0]
    for i in range(1, len(prices)):
        ema[i] = prices[i] * k + ema[i - 1] * (1 - k)
    return ema


def _rsi(closes: np.ndarray, period: int = 14) -> float:
    """Relative Strength Index (last value)."""
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _macd(closes: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
    """
    MACD line, signal line, histogram (last values).
    Returns (macd, signal, histogram).
    """
    if len(closes) < slow + signal:
        return 0.0, 0.0, 0.0
    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return float(macd_line[-1]), float(signal_line[-1]), float(histogram[-1])


def _bollinger_bands(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
    """
    Returns (upper_band, middle_band, lower_band) — last values.
    """
    if len(closes) < period:
        mid = float(closes[-1])
        return mid, mid, mid
    window = closes[-period:]
    mid = float(np.mean(window))
    std = float(np.std(window))
    return mid + std_dev * std, mid, mid - std_dev * std


def _atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """Average True Range — measure of volatility."""
    if len(closes) < 2:
        return 0.0
    tr = np.maximum(
        highs[1:] - lows[1:],
        np.maximum(
            np.abs(highs[1:] - closes[:-1]),
            np.abs(lows[1:] - closes[:-1]),
        ),
    )
    return float(np.mean(tr[-period:])) if len(tr) >= period else float(np.mean(tr))


def _adx(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """
    Simplified Average Directional Index (trend strength 0–100).
    Values above 25 indicate a trending market.
    """
    if len(closes) < period + 1:
        return 20.0
    plus_dm = np.maximum(highs[1:] - highs[:-1], 0)
    minus_dm = np.maximum(lows[:-1] - lows[1:], 0)
    # Zero out where the other direction is larger
    mask = plus_dm < minus_dm
    plus_dm[mask] = 0
    mask2 = minus_dm <= plus_dm
    minus_dm[mask2] = 0

    tr = np.maximum(highs[1:] - lows[1:], np.abs(highs[1:] - closes[:-1]))
    tr = np.maximum(tr, np.abs(lows[1:] - closes[:-1]))

    tr_s = np.mean(tr[-period:])
    if tr_s == 0:
        return 20.0

    di_plus = 100 * np.mean(plus_dm[-period:]) / tr_s
    di_minus = 100 * np.mean(minus_dm[-period:]) / tr_s
    dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus + 1e-9)
    return float(dx)


# ─────────────────────────────────────────────────────────────────────────────
# Pattern detection
# ─────────────────────────────────────────────────────────────────────────────

def _detect_pattern(opens: np.ndarray, closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> Optional[str]:
    """Detect the most recent candlestick pattern."""
    if len(closes) < 3:
        return None

    o, c, h, low = opens[-1], closes[-1], highs[-1], lows[-1]
    po, pc = opens[-2], closes[-2]
    body = abs(c - o)
    prev_body = abs(pc - po)
    candle_range = h - low

    # Doji — body is < 10% of the total range
    if candle_range > 0 and body / candle_range < 0.1:
        return "Doji"

    # Hammer — small body at the top, long lower wick
    lower_wick = min(o, c) - low
    upper_wick = h - max(o, c)
    if lower_wick > 2 * body and upper_wick < body:
        return "Hammer (Bullish)"

    # Shooting star — small body at the bottom, long upper wick
    if upper_wick > 2 * body and lower_wick < body:
        return "Shooting Star (Bearish)"

    # Bullish engulfing
    if pc > po and c > o and c > po and o < pc:
        return "Bullish Engulfing"

    # Bearish engulfing
    if pc < po and c < o and c < po and o > pc:
        return "Bearish Engulfing"

    # Morning star (3-candle)
    if len(closes) >= 3:
        o2, c2 = opens[-3], closes[-3]
        if c2 < o2 and abs(pc - po) < prev_body * 0.3 and c > o:
            return "Morning Star (Bullish)"

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Signal generator
# ─────────────────────────────────────────────────────────────────────────────

class AIEngine:
    """
    Rule-based signal engine with a weighted scoring system.

    Scores range from -1.0 (strong SELL) to +1.0 (strong BUY).
    Scores between -threshold and +threshold produce WAIT.
    """

    BUY_THRESHOLD  = 0.35
    SELL_THRESHOLD = -0.35

    def __init__(self, client: DerivClient):
        self.client = client

    async def analyse(self, symbol: str, granularity: int = 60) -> Signal:
        """
        Full market analysis for *symbol*.

        :param granularity: candle size in seconds.
        """
        try:
            candles = await self.client.get_candles(symbol, granularity=granularity, count=100)
        except Exception as e:
            logger.error("ai_engine.candle_fetch_failed", symbol=symbol, error=str(e))
            return Signal(symbol=symbol, signal="WAIT", confidence=0.0,
                          reason="Unable to fetch market data", trend="SIDEWAYS",
                          volatility="UNKNOWN")

        if len(candles) < 30:
            return Signal(symbol=symbol, signal="WAIT", confidence=0.0,
                          reason="Insufficient candle data", trend="SIDEWAYS",
                          volatility="UNKNOWN")

        opens  = np.array([float(c["open"])  for c in candles])
        highs  = np.array([float(c["high"])  for c in candles])
        lows   = np.array([float(c["low"])   for c in candles])
        closes = np.array([float(c["close"]) for c in candles])

        current_price = closes[-1]

        # ── Compute indicators ────────────────────────────────────────────────
        rsi_val = _rsi(closes)
        macd_val, macd_sig, macd_hist = _macd(closes)
        bb_upper, bb_mid, bb_lower = _bollinger_bands(closes)
        ema_20 = _ema(closes, 20)[-1]
        ema_50 = _ema(closes, 50)[-1] if len(closes) >= 50 else ema_20
        atr_val = _atr(highs, lows, closes)
        adx_val = _adx(highs, lows, closes)

        # ── Scoring ───────────────────────────────────────────────────────────
        score = 0.0
        reasons: List[str] = []

        # RSI  (weight 0.25)
        if rsi_val < 30:
            score += 0.25
            reasons.append(f"RSI oversold ({rsi_val:.1f})")
        elif rsi_val > 70:
            score -= 0.25
            reasons.append(f"RSI overbought ({rsi_val:.1f})")

        # MACD crossover  (weight 0.25)
        if macd_hist > 0 and macd_val > macd_sig:
            score += 0.25
            reasons.append("MACD bullish crossover")
        elif macd_hist < 0 and macd_val < macd_sig:
            score -= 0.25
            reasons.append("MACD bearish crossover")

        # EMA trend  (weight 0.20)
        if ema_20 > ema_50 and current_price > ema_20:
            score += 0.20
            reasons.append("Price above EMA20 > EMA50")
        elif ema_20 < ema_50 and current_price < ema_20:
            score -= 0.20
            reasons.append("Price below EMA20 < EMA50")

        # Bollinger Bands  (weight 0.20)
        if current_price < bb_lower:
            score += 0.20
            reasons.append("Price below lower Bollinger Band")
        elif current_price > bb_upper:
            score -= 0.20
            reasons.append("Price above upper Bollinger Band")

        # ADX trend strength filter  (weight 0.10)
        if adx_val < 20:
            score *= 0.5
            reasons.append(f"Weak trend (ADX {adx_val:.1f}) — signal reduced")
        else:
            reasons.append(f"Trend strength: ADX {adx_val:.1f}")

        # ── Pattern detection ─────────────────────────────────────────────────
        pattern = _detect_pattern(opens, closes, highs, lows)
        if pattern:
            if "Bullish" in pattern or "Hammer" in pattern or "Morning" in pattern:
                score += 0.10
                reasons.append(f"Pattern: {pattern}")
            elif "Bearish" in pattern or "Shooting" in pattern:
                score -= 0.10
                reasons.append(f"Pattern: {pattern}")

        # ── Volatility classification ─────────────────────────────────────────
        atr_pct = (atr_val / current_price) * 100
        if atr_pct > 2.0:
            volatility = "HIGH"
        elif atr_pct > 0.8:
            volatility = "MEDIUM"
        else:
            volatility = "LOW"

        # ── Trend ─────────────────────────────────────────────────────────────
        if ema_20 > ema_50:
            trend = "BULLISH"
        elif ema_20 < ema_50:
            trend = "BEARISH"
        else:
            trend = "SIDEWAYS"

        # ── Final decision ────────────────────────────────────────────────────
        confidence = min(abs(score), 1.0)

        if score >= self.BUY_THRESHOLD:
            decision = "BUY"
        elif score <= self.SELL_THRESHOLD:
            decision = "SELL"
        else:
            decision = "WAIT"

        reason_text = "; ".join(reasons) if reasons else "Mixed signals — no clear direction"

        logger.info(
            "ai_engine.signal",
            symbol=symbol,
            signal=decision,
            confidence=round(confidence, 3),
            score=round(score, 3),
            trend=trend,
            volatility=volatility,
        )

        return Signal(
            symbol=symbol,
            signal=decision,
            confidence=round(confidence, 3),
            reason=reason_text,
            trend=trend,
            volatility=volatility,
            pattern=pattern,
            entry_price=current_price,
        )

    async def batch_analyse(self, symbols: List[str], granularity: int = 60) -> Dict[str, Signal]:
        """Analyse multiple symbols concurrently."""
        tasks = [self.analyse(s, granularity) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        output: Dict[str, Signal] = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error("ai_engine.batch_error", symbol=symbol, error=str(result))
                output[symbol] = Signal(
                    symbol=symbol, signal="WAIT", confidence=0.0,
                    reason=str(result), trend="SIDEWAYS", volatility="UNKNOWN"
                )
            else:
                output[symbol] = result
        return output
