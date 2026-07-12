"""
AI Trading Signal Engine — MA Bias Basket Strategy

Strategy logic (ported from MA_Bias_Basket_EA.mq5):

  BIAS (4H timeframe):
    - EMA(5, Close) > EMA(13, Close) AND ADX(14) >= 20 → BULLISH bias
    - EMA(5, Close) < EMA(13, Close) AND ADX(14) >= 20 → BEARISH bias

  ENTRY (15M timeframe):
    - EMA(5, Typical) > SMA(50, Typical) AND last candle closed ABOVE EMA(5) → BUY trigger
    - EMA(5, Typical) < SMA(50, Typical) AND last candle closed BELOW EMA(5) → SELL trigger

  SIGNAL:
    - BULLISH bias + BUY trigger  → BUY
    - BEARISH bias + SELL trigger → SELL
    - Any mismatch                → WAIT

  EMERGENCY EXIT signal:
    - BUY basket open + candle closes below SMA20 or SMA50 → close signal
    - SELL basket open + candle closes above SMA20 or SMA50 → close signal
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
# Technical indicator helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ema(prices: np.ndarray, period: int) -> np.ndarray:
    """Exponential Moving Average."""
    k = 2.0 / (period + 1)
    ema = np.zeros_like(prices)
    ema[0] = prices[0]
    for i in range(1, len(prices)):
        ema[i] = prices[i] * k + ema[i - 1] * (1 - k)
    return ema


def _sma(prices: np.ndarray, period: int) -> np.ndarray:
    """Simple Moving Average."""
    result = np.full_like(prices, np.nan)
    for i in range(period - 1, len(prices)):
        result[i] = np.mean(prices[i - period + 1: i + 1])
    return result


def _typical_price(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    """Typical Price = (High + Low + Close) / 3"""
    return (highs + lows + closes) / 3.0


def _adx(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """
    Average Directional Index — trend strength (0-100).
    Values >= 20 indicate a trending market.
    """
    if len(closes) < period + 2:
        return 15.0

    plus_dm = np.maximum(highs[1:] - highs[:-1], 0.0)
    minus_dm = np.maximum(lows[:-1] - lows[1:], 0.0)

    mask_plus = plus_dm < minus_dm
    plus_dm[mask_plus] = 0.0
    mask_minus = minus_dm <= plus_dm
    minus_dm[mask_minus] = 0.0

    tr = np.maximum(highs[1:] - lows[1:], np.abs(highs[1:] - closes[:-1]))
    tr = np.maximum(tr, np.abs(lows[1:] - closes[:-1]))

    tr_smooth = np.mean(tr[-period:])
    if tr_smooth == 0:
        return 15.0

    di_plus = 100.0 * np.mean(plus_dm[-period:]) / tr_smooth
    di_minus = 100.0 * np.mean(minus_dm[-period:]) / tr_smooth
    denom = di_plus + di_minus
    if denom == 0:
        return 15.0

    dx = 100.0 * abs(di_plus - di_minus) / denom
    return float(dx)


def _atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
    """Average True Range — volatility measure."""
    if len(closes) < 2:
        return 0.0
    tr = np.maximum(
        highs[1:] - lows[1:],
        np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])),
    )
    return float(np.mean(tr[-period:])) if len(tr) >= period else float(np.mean(tr))


# ─────────────────────────────────────────────────────────────────────────────
# MA Bias Basket AI Engine
# ─────────────────────────────────────────────────────────────────────────────

class AIEngine:
    """
    MA Bias Basket strategy ported from MQL5 to Python.

    Bias timeframe  : 4H  (EMA5/EMA13 on Close + ADX14 >= 20)
    Entry timeframe : 15M (EMA5 vs SMA50 on Typical Price + candle close position)
    Exit monitor    : 15M SMA20 and SMA50 for emergency exit signals
    """

    # Strategy parameters (matching the MQL5 EA defaults)
    BIAS_FAST_PERIOD = 5
    BIAS_SLOW_PERIOD = 13
    ADX_PERIOD = 14
    ADX_THRESHOLD = 20.0

    ENTRY_FAST_PERIOD = 5    # EMA on Typical Price
    ENTRY_SLOW_PERIOD = 50   # SMA on Typical Price
    EXIT_SMA_PERIOD = 20     # SMA20 for emergency exit

    def __init__(self, client: DerivClient):
        self.client = client

    async def analyse(self, symbol: str, granularity: int = 60) -> Signal:
        """
        Full MA Bias Basket analysis for *symbol*.

        Fetches both 4H and 15M candles then applies the strategy logic.
        granularity parameter is kept for API compatibility but we fetch
        both required timeframes internally.
        """
        # Fetch 4H candles (granularity = 14400 seconds)
        try:
            candles_4h = await self.client.get_candles(
                symbol, granularity=14400, count=100
            )
        except Exception as e:
            logger.error("ai_engine.4h_fetch_failed", symbol=symbol, error=str(e))
            return self._wait_signal(symbol, "Unable to fetch 4H market data")

        # Fetch 15M candles (granularity = 900 seconds)
        try:
            candles_15m = await self.client.get_candles(
                symbol, granularity=900, count=100
            )
        except Exception as e:
            logger.error("ai_engine.15m_fetch_failed", symbol=symbol, error=str(e))
            return self._wait_signal(symbol, "Unable to fetch 15M market data")

        if len(candles_4h) < 30 or len(candles_15m) < 60:
            return self._wait_signal(symbol, "Insufficient candle data")

        # ── 4H arrays ────────────────────────────────────────────────────────
        closes_4h = np.array([float(c["close"]) for c in candles_4h])
        highs_4h  = np.array([float(c["high"])  for c in candles_4h])
        lows_4h   = np.array([float(c["low"])   for c in candles_4h])

        # ── 15M arrays ───────────────────────────────────────────────────────
        opens_15m  = np.array([float(c["open"])  for c in candles_15m])
        closes_15m = np.array([float(c["close"]) for c in candles_15m])
        highs_15m  = np.array([float(c["high"])  for c in candles_15m])
        lows_15m   = np.array([float(c["low"])   for c in candles_15m])

        typical_15m = _typical_price(highs_15m, lows_15m, closes_15m)

        # ── 4H indicators ─────────────────────────────────────────────────────
        ema5_4h  = _ema(closes_4h, self.BIAS_FAST_PERIOD)
        ema13_4h = _ema(closes_4h, self.BIAS_SLOW_PERIOD)
        adx_4h   = _adx(highs_4h, lows_4h, closes_4h, self.ADX_PERIOD)

        # Use second-to-last bar (last CLOSED bar — same as MQL5 index 1)
        bias_fast = ema5_4h[-2]
        bias_slow = ema13_4h[-2]

        # ── 4H Bias determination ─────────────────────────────────────────────
        adx_ok = adx_4h >= self.ADX_THRESHOLD
        bias_bull = bias_fast > bias_slow and adx_ok
        bias_bear = bias_fast < bias_slow and adx_ok

        # ── 15M indicators ───────────────────────────────────────────────────
        ema5_15m  = _ema(typical_15m, self.ENTRY_FAST_PERIOD)
        sma50_15m = _sma(typical_15m, self.ENTRY_SLOW_PERIOD)
        sma20_15m = _sma(typical_15m, self.EXIT_SMA_PERIOD)

        # Last closed 15M bar
        entry_fast  = ema5_15m[-2]
        entry_slow  = sma50_15m[-2]
        sma20_last  = sma20_15m[-2]
        close_15m_last = closes_15m[-2]

        # ── Entry triggers ───────────────────────────────────────────────────
        price_above_fast = close_15m_last > entry_fast
        price_below_fast = close_15m_last < entry_fast

        buy_trigger  = (entry_fast > entry_slow) and price_above_fast
        sell_trigger = (entry_fast < entry_slow) and price_below_fast

        # ── Final signal ─────────────────────────────────────────────────────
        if bias_bull and buy_trigger:
            signal = "BUY"
            reasons = [
                f"4H EMA{self.BIAS_FAST_PERIOD}({bias_fast:.5f}) > EMA{self.BIAS_SLOW_PERIOD}({bias_slow:.5f}) — BULLISH bias",
                f"ADX({adx_4h:.1f}) >= {self.ADX_THRESHOLD} — trend confirmed",
                f"15M EMA{self.ENTRY_FAST_PERIOD}({entry_fast:.5f}) > SMA{self.ENTRY_SLOW_PERIOD}({entry_slow:.5f})",
                f"15M candle closed above EMA{self.ENTRY_FAST_PERIOD} ({close_15m_last:.5f})",
            ]
            confidence = self._calc_confidence(adx_4h, bias_fast, bias_slow, entry_fast, entry_slow)
            trend = "BULLISH"

        elif bias_bear and sell_trigger:
            signal = "SELL"
            reasons = [
                f"4H EMA{self.BIAS_FAST_PERIOD}({bias_fast:.5f}) < EMA{self.BIAS_SLOW_PERIOD}({bias_slow:.5f}) — BEARISH bias",
                f"ADX({adx_4h:.1f}) >= {self.ADX_THRESHOLD} — trend confirmed",
                f"15M EMA{self.ENTRY_FAST_PERIOD}({entry_fast:.5f}) < SMA{self.ENTRY_SLOW_PERIOD}({entry_slow:.5f})",
                f"15M candle closed below EMA{self.ENTRY_FAST_PERIOD} ({close_15m_last:.5f})",
            ]
            confidence = self._calc_confidence(adx_4h, bias_slow, bias_fast, entry_slow, entry_fast)
            trend = "BEARISH"

        else:
            # Build WAIT reasons
            reasons = []
            if not adx_ok:
                reasons.append(f"ADX({adx_4h:.1f}) < {self.ADX_THRESHOLD} — trend too weak")
            if not bias_bull and not bias_bear:
                reasons.append("4H EMAs are too close — no clear bias")
            if bias_bull and not buy_trigger:
                reasons.append("4H is bullish but 15M entry not confirmed yet")
            if bias_bear and not sell_trigger:
                reasons.append("4H is bearish but 15M entry not confirmed yet")
            if not reasons:
                reasons.append("Bias and entry timeframes do not align")

            signal = "WAIT"
            confidence = 0.0
            trend = "BULLISH" if bias_fast > bias_slow else "BEARISH" if bias_fast < bias_slow else "SIDEWAYS"

        # ── Volatility ───────────────────────────────────────────────────────
        atr = _atr(highs_15m, lows_15m, closes_15m)
        current_price = closes_15m[-1]
        atr_pct = (atr / current_price) * 100 if current_price > 0 else 0

        if atr_pct > 2.0:
            volatility = "HIGH"
        elif atr_pct > 0.8:
            volatility = "MEDIUM"
        else:
            volatility = "LOW"

        # ── Emergency exit note ──────────────────────────────────────────────
        pattern = None
        if signal == "BUY" or (signal == "WAIT" and bias_bull):
            if close_15m_last < sma20_last or close_15m_last < entry_slow:
                pattern = "Emergency Exit: Close < SMA20 or SMA50"
        elif signal == "SELL" or (signal == "WAIT" and bias_bear):
            if close_15m_last > sma20_last or close_15m_last > entry_slow:
                pattern = "Emergency Exit: Close > SMA20 or SMA50"

        reason_text = "; ".join(reasons)

        logger.info(
            "ai_engine.signal",
            symbol=symbol,
            signal=signal,
            confidence=round(confidence, 3),
            adx=round(adx_4h, 1),
            bias="BULL" if bias_bull else "BEAR" if bias_bear else "FLAT",
            trend=trend,
            volatility=volatility,
        )

        return Signal(
            symbol=symbol,
            signal=signal,
            confidence=round(confidence, 3),
            reason=reason_text,
            trend=trend,
            volatility=volatility,
            pattern=pattern,
            entry_price=current_price,
        )

    def _calc_confidence(
        self,
        adx: float,
        fast_bias: float,
        slow_bias: float,
        fast_entry: float,
        slow_entry: float,
    ) -> float:
        """
        Confidence score based on:
        - How far apart the bias EMAs are (stronger separation = higher confidence)
        - ADX strength (stronger trend = higher confidence)
        - How far entry EMAs are separated
        """
        # Bias separation score (0-0.4)
        bias_sep = abs(fast_bias - slow_bias) / slow_bias if slow_bias != 0 else 0
        bias_score = min(bias_sep * 100, 0.4)

        # ADX score (0-0.4): ADX 20=0.0, ADX 40=0.4
        adx_score = min((adx - self.ADX_THRESHOLD) / 50.0, 0.4)
        adx_score = max(adx_score, 0.0)

        # Entry separation score (0-0.2)
        entry_sep = abs(fast_entry - slow_entry) / slow_entry if slow_entry != 0 else 0
        entry_score = min(entry_sep * 100, 0.2)

        total = bias_score + adx_score + entry_score
        return min(round(total, 3), 1.0)

    def _wait_signal(self, symbol: str, reason: str) -> Signal:
        return Signal(
            symbol=symbol,
            signal="WAIT",
            confidence=0.0,
            reason=reason,
            trend="SIDEWAYS",
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
