"""
AI Trading Signal Engine — 1-Minute Microtrading Strategy

Strategy logic:

  BUY signal — all 3 must be true simultaneously:
    1. EMA 3 crosses ABOVE BB middle band (18-period SMA)
    2. MACD Histogram value > 0
    3. RSI 14 > 50

  SELL signal — all 3 must be true simultaneously:
    1. EMA 3 crosses BELOW BB middle band
    2. MACD Histogram value < 0
    3. RSI 14 < 50

  EXIT logic:
    - Trailing stop on winning trades (default 2 pips)
    - No hard take-profit (scalp and exit fast)
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np

from app.core.logging import get_logger
from app.services.deriv_client import DerivClient

logger = get_logger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# Data structures
# ────────────────────────────────────────────────────────────────────────────

@dataclass
class Signal:
    symbol: str
    signal: str                       # BUY | SELL | WAIT
    confidence: float                 # 0.0 – 1.0
    reason: str
    ema3_value: Optional[float] = None
    bb_middle: Optional[float] = None
    macd_histogram: Optional[float] = None
    rsi_value: Optional[float] = None
    volatility: str = "MEDIUM"
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ────────────────────────────────────────────────────────────────────────────
# Technical indicator helpers
# ────────────────────────────────────────────────────────────────────────────

def _ema(prices: np.ndarray, period: int) -> np.ndarray:
    """Exponential Moving Average."""
    if len(prices) < period:
        return np.array([prices[0]] * len(prices))
    k = 2.0 / (period + 1)
    ema = np.zeros_like(prices)
    ema[0] = prices[0]
    for i in range(1, len(prices)):
        ema[i] = prices[i] * k + ema[i - 1] * (1 - k)
    return ema


def _sma(prices: np.ndarray, period: int) -> np.ndarray:
    """Simple Moving Average."""
    if len(prices) < period:
        return np.array([np.mean(prices[:i+1]) if i >= 0 else prices[0] for i in range(len(prices))])
    result = np.full_like(prices, np.nan, dtype=float)
    for i in range(period - 1, len(prices)):
        result[i] = np.mean(prices[i - period + 1: i + 1])
    return result


def _bb_bands(
    prices: np.ndarray, period: int = 18, std_dev: float = 2.0, method: str = "SMA"
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Bollinger Bands — returns (upper, middle, lower).
    method: "SMA" or "EMA"
    """
    if method.upper() == "EMA":
        middle = _ema(prices, period)
    else:
        middle = _sma(prices, period)

    # Calculate standard deviation
    std = np.zeros_like(prices)
    for i in range(period - 1, len(prices)):
        std[i] = np.std(prices[i - period + 1: i + 1])

    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)

    return upper, middle, lower


def _macd_histogram(
    prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    MACD Histogram — returns (macd_line, signal_line, histogram).
    histogram = macd_line - signal_line
    """
    if len(prices) < slow + signal:
        return np.zeros_like(prices), np.zeros_like(prices), np.zeros_like(prices)

    ema_fast = _ema(prices, fast)
    ema_slow = _ema(prices, slow)
    macd_line = ema_fast - ema_slow

    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def _rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """Relative Strength Index (0-100)."""
    if len(prices) < period + 1:
        return np.full_like(prices, 50.0)

    deltas = np.diff(prices)
    seed = deltas[:period+1]

    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0

    rsi = np.zeros_like(prices)
    rsi[:period] = 100.0 - 100.0 / (1.0 + rs) if rs > 0 else 50.0

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.0
        else:
            upval = 0.0
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period

        rs = up / down if down != 0 else 0
        rsi[i] = 100.0 - 100.0 / (1.0 + rs) if rs > 0 else 50.0

    return rsi


def _atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """Average True Range — volatility measure."""
    if len(closes) < 2:
        return 0.0
    tr = np.maximum(
        highs[1:] - lows[1:],
        np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])),
    )
    return float(np.mean(tr[-period:])) if len(tr) >= period else float(np.mean(tr))


# ────────────────────────────────────────────────────────────────────────────
# 1-Minute Microtrading AI Engine
# ────────────────────────────────────────────────────────────────────────────

class AIEngine:
    """
    1-Minute Microtrading strategy — fully configurable parameters.
    Indicators: EMA 3, Bollinger Bands 18, MACD (9, 12, 26), RSI 14
    """

    def __init__(self, client: DerivClient, settings=None):
        self.client = client
        self._s = settings

    def _get(self, attr: str, default):
        if self._s is not None:
            return getattr(self._s, attr, default)
        return default

    async def analyse(self, symbol: str, granularity: int = 60) -> Signal:
        """Full 1M microtrading analysis using configured or default parameters."""

        # ── Load parameters ────────────────────────────────────────────────────
        ema_period = self._get("ema_fast_period", 3)
        ema_price = self._get("ema_applied_price", "CLOSE")

        bb_period = self._get("bb_period", 18)
        bb_std_dev = self._get("bb_std_dev", 2.0)
        bb_method = self._get("bb_method", "SMA")

        macd_fast = self._get("macd_fast", 12)
        macd_slow = self._get("macd_slow", 26)
        macd_signal = self._get("macd_signal", 9)

        rsi_period = self._get("rsi_period", 14)
        rsi_overbought = self._get("rsi_overbought", 70.0)
        rsi_oversold = self._get("rsi_oversold", 30.0)

        # ── Fetch 1M candles ───────────────────────────────────────────────────
        try:
            candles = await self.client.get_candles(
                symbol, granularity=60, count=100
            )
        except Exception as e:
            logger.error("ai_engine.candle_fetch_failed", symbol=symbol, error=str(e))
            return self._wait_signal(symbol, f"Unable to fetch candles: {str(e)}")

        if len(candles) < max(bb_period + 5, macd_slow + macd_signal + 5, rsi_period + 2):
            return self._wait_signal(symbol, "Insufficient candle data")

        # ── Build numpy arrays ────────────────────────────────────────────────
        opens = np.array([float(c["open"]) for c in candles])
        highs = np.array([float(c["high"]) for c in candles])
        lows = np.array([float(c["low"]) for c in candles])
        closes = np.array([float(c["close"]) for c in candles])

        # Apply price type for EMA
        if ema_price.upper() == "OPEN":
            ema_prices = opens
        elif ema_price.upper() == "HIGH":
            ema_prices = highs
        elif ema_price.upper() == "LOW":
            ema_prices = lows
        elif ema_price.upper() == "MEDIAN":
            ema_prices = (highs + lows) / 2.0
        elif ema_price.upper() == "TYPICAL":
            ema_prices = (highs + lows + closes) / 3.0
        elif ema_price.upper() == "WEIGHTED":
            ema_prices = (highs + lows + closes + closes) / 4.0
        else:
            ema_prices = closes

        # ── Calculate indicators ───────────────────────────────────────────────
        ema3 = _ema(closes, ema_period)
        _, bb_middle, _ = _bb_bands(closes, bb_period, bb_std_dev, bb_method)
        macd_line, signal_line, macd_hist = _macd_histogram(closes, macd_fast, macd_slow, macd_signal)
        rsi = _rsi(closes, rsi_period)

        # Get current and previous values (last 2 closed candles)
        ema3_now = ema3[-2]
        ema3_prev = ema3[-3] if len(ema3) >= 3 else ema3[-2]

        bb_mid_now = bb_middle[-2] if not np.isnan(bb_middle[-2]) else closes[-2]
        bb_mid_prev = bb_middle[-3] if len(bb_middle) >= 3 and not np.isnan(bb_middle[-3]) else bb_mid_now

        macd_hist_now = macd_hist[-2] if len(macd_hist) > 0 else 0.0
        rsi_now = rsi[-2] if not np.isnan(rsi[-2]) else 50.0

        # ── Detect EMA/BB crossover ────────────────────────────────────────────
        ema_above_bb_now = ema3_now > bb_mid_now
        ema_above_bb_prev = ema3_prev > bb_mid_prev

        bullish_cross = (not ema_above_bb_prev) and ema_above_bb_now
        bearish_cross = ema_above_bb_prev and (not ema_above_bb_now)

        # ── Signal logic ───────────────────────────────────────────────────────
        macd_positive = macd_hist_now > 0
        macd_negative = macd_hist_now < 0
        rsi_high = rsi_now > 50  # Not necessarily > overbought
        rsi_low = rsi_now < 50

        signal = "WAIT"
        confidence = 0.0
        reason_parts = []

        if bullish_cross and macd_positive and rsi_high:
            signal = "BUY"
            reason_parts = [
                f"EMA({ema_period}) crossed above BB({bb_period}) middle",
                f"MACD histogram > 0 ({macd_hist_now:.6f})",
                f"RSI({rsi_period}) > 50 ({rsi_now:.1f})",
            ]
            confidence = self._calc_confidence(bullish_cross, macd_positive, rsi_high)

        elif bearish_cross and macd_negative and rsi_low:
            signal = "SELL"
            reason_parts = [
                f"EMA({ema_period}) crossed below BB({bb_period}) middle",
                f"MACD histogram < 0 ({macd_hist_now:.6f})",
                f"RSI({rsi_period}) < 50 ({rsi_now:.1f})",
            ]
            confidence = self._calc_confidence(bearish_cross, macd_negative, rsi_low)

        else:
            # WAIT — diagnose why
            if not bullish_cross and not bearish_cross:
                reason_parts.append(f"No EMA/BB crossover (EMA: {ema3_now:.5f}, BB: {bb_mid_now:.5f})")
            if not macd_positive and not macd_negative:
                reason_parts.append(f"MACD histogram near zero ({macd_hist_now:.6f})")
            if signal == "WAIT" and (bullish_cross or bearish_cross):
                if bullish_cross and not (macd_positive and rsi_high):
                    parts = []
                    if not macd_positive:
                        parts.append(f"MACD not positive ({macd_hist_now:.6f})")
                    if not rsi_high:
                        parts.append(f"RSI not > 50 ({rsi_now:.1f})")
                    reason_parts.append(f"Bullish cross but: {', '.join(parts)}")
                elif bearish_cross and not (macd_negative and rsi_low):
                    parts = []
                    if not macd_negative:
                        parts.append(f"MACD not negative ({macd_hist_now:.6f})")
                    if not rsi_low:
                        parts.append(f"RSI not < 50 ({rsi_now:.1f})")
                    reason_parts.append(f"Bearish cross but: {', '.join(parts)}")

            if not reason_parts:
                reason_parts.append("Waiting for alignment of all 3 indicators")

        # ── Volatility ─────────────────────────────────────────────────────────
        atr = _atr(highs, lows, closes, period=14)
        current_price = closes[-1]
        atr_pct = (atr / current_price) * 100 if current_price > 0 else 0

        if atr_pct > 2.0:
            volatility = "HIGH"
        elif atr_pct > 0.8:
            volatility = "MEDIUM"
        else:
            volatility = "LOW"

        reason_text = "; ".join(reason_parts)

        logger.info(
            "ai_engine.signal",
            symbol=symbol,
            signal=signal,
            confidence=round(confidence, 3),
            ema3=round(ema3_now, 5),
            bb_mid=round(bb_mid_now, 5),
            macd_hist=round(macd_hist_now, 6),
            rsi=round(rsi_now, 1),
            volatility=volatility,
        )

        return Signal(
            symbol=symbol,
            signal=signal,
            confidence=round(confidence, 3),
            reason=reason_text,
            ema3_value=round(ema3_now, 5),
            bb_middle=round(bb_mid_now, 5),
            macd_histogram=round(macd_hist_now, 6),
            rsi_value=round(rsi_now, 1),
            volatility=volatility,
        )

    def _calc_confidence(self, crossover: bool, macd_ok: bool, rsi_ok: bool) -> float:
        """
        Confidence score (0-1).
        All 3 conditions met = high confidence.
        """
        score = 0.0
        if crossover:
            score += 0.4
        if macd_ok:
            score += 0.3
        if rsi_ok:
            score += 0.3
        return min(round(score, 3), 1.0)

    def _wait_signal(self, symbol: str, reason: str) -> Signal:
        return Signal(
            symbol=symbol,
            signal="WAIT",
            confidence=0.0,
            reason=reason,
            volatility="UNKNOWN",
        )

    async def batch_analyse(self, symbols: List[str], granularity: int = 60) -> Dict[str, Signal]:
        """Analyse multiple symbols concurrently."""
        tasks = [self.analyse(s, granularity) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        output: Dict[str, Signal] = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error("ai_engine.batch_error", symbol=symbol, error=str(result))
                output[symbol] = self._wait_signal(symbol, str(result))
            else:
                output[symbol] = result
        return output
