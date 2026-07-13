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
from typing import Dict, List, Optional

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
    MA Bias Basket strategy — fully configurable parameters.
    All defaults match the original MQL5 EA inputs.
    """

    def __init__(self, client: DerivClient, settings=None):
        self.client = client
        self._s = settings  # StrategySettings ORM object or None (uses defaults)

    def _get(self, attr: str, default):
        """Get setting value from DB settings or fall back to default."""
        if self._s is not None:
            return getattr(self._s, attr, default)
        return default

    async def analyse(self, symbol: str, granularity: int = 60) -> Signal:
        """Full MA Bias Basket analysis using configured or default parameters."""

        # ── Load parameters ──────────────────────────────────────────────────
        bias_tf        = self._get("bias_timeframe", 14400)
        bias_fast_p    = self._get("bias_fast_period", 5)
        bias_slow_p    = self._get("bias_slow_period", 13)
        bias_method    = self._get("bias_ma_method", "EMA")
        bias_price     = self._get("bias_applied_price", "CLOSE")
        adx_enabled    = self._get("adx_enabled", True)
        adx_period     = self._get("adx_period", 14)
        adx_threshold  = self._get("adx_threshold", 20.0)
        entry_tf       = self._get("entry_timeframe", 900)
        entry_fast_p   = self._get("entry_fast_period", 5)
        entry_fast_m   = self._get("entry_fast_method", "EMA")
        entry_slow_p   = self._get("entry_slow_period", 50)
        entry_slow_m   = self._get("entry_slow_method", "SMA")
        entry_price    = self._get("entry_applied_price", "TYPICAL")
        exit_enabled   = self._get("emergency_exit_enabled", True)
        exit_sma_p     = self._get("exit_sma_period", 50)
        require_confirm = self._get("require_candle_confirmation", False)
        # Fetch 4H candles (bias timeframe)
        try:
            candles_4h = await self.client.get_candles(
                symbol, granularity=bias_tf, count=100
            )
        except Exception as e:
            logger.error("ai_engine.4h_fetch_failed", symbol=symbol, error=str(e))
            return self._wait_signal(symbol, "Unable to fetch bias timeframe data")

        # Fetch 15M candles (entry timeframe)
        try:
            candles_15m = await self.client.get_candles(
                symbol, granularity=entry_tf, count=100
            )
        except Exception as e:
            logger.error("ai_engine.15m_fetch_failed", symbol=symbol, error=str(e))
            return self._wait_signal(symbol, "Unable to fetch entry timeframe data")

        if len(candles_4h) < 30 or len(candles_15m) < 60:
            return self._wait_signal(symbol, "Insufficient candle data")

        # ── Build numpy arrays ────────────────────────────────────────────────
        opens_4h  = np.array([float(c["open"])  for c in candles_4h])
        closes_4h = np.array([float(c["close"]) for c in candles_4h])
        highs_4h  = np.array([float(c["high"])  for c in candles_4h])
        lows_4h   = np.array([float(c["low"])   for c in candles_4h])

        opens_15m  = np.array([float(c["open"])  for c in candles_15m])
        closes_15m = np.array([float(c["close"]) for c in candles_15m])
        highs_15m  = np.array([float(c["high"])  for c in candles_15m])
        lows_15m   = np.array([float(c["low"])   for c in candles_15m])

        # ── Applied price helpers ─────────────────────────────────────────────
        def _apply_price(o, h, lo, c, price_type: str) -> np.ndarray:
            p = price_type.upper()
            if p == "OPEN":
                return o
            if p == "HIGH":
                return h
            if p == "LOW":
                return lo
            if p == "MEDIAN":
                return (h + lo) / 2.0
            if p == "TYPICAL":
                return (h + lo + c) / 3.0
            if p == "WEIGHTED":
                return (h + lo + c + c) / 4.0
            return c  # default CLOSE

        def _apply_ma(prices: np.ndarray, period: int, method: str) -> np.ndarray:
            m = method.upper()
            if m == "SMA":
                return _sma(prices, period)
            if m == "WMA":
                result = np.zeros_like(prices)
                for i in range(period - 1, len(prices)):
                    weights = np.arange(1, period + 1, dtype=float)
                    result[i] = np.dot(prices[i - period + 1: i + 1], weights) / weights.sum()
                return result
            if m == "SMMA":
                result = np.zeros_like(prices)
                result[period - 1] = np.mean(prices[:period])
                for i in range(period, len(prices)):
                    result[i] = (result[i - 1] * (period - 1) + prices[i]) / period
                return result
            return _ema(prices, period)  # default EMA

        # ── 4H indicator calculations ─────────────────────────────────────────
        bias_price_arr = _apply_price(opens_4h, highs_4h, lows_4h, closes_4h, bias_price)
        ema_fast_4h = _apply_ma(bias_price_arr, bias_fast_p, bias_method)
        ema_slow_4h = _apply_ma(bias_price_arr, bias_slow_p, bias_method)
        adx_4h = _adx(highs_4h, lows_4h, closes_4h, adx_period)

        bias_fast = ema_fast_4h[-2]
        bias_slow = ema_slow_4h[-2]

        # ── 4H Bias ───────────────────────────────────────────────────────────
        adx_ok = (not adx_enabled) or (adx_4h >= adx_threshold)
        bias_bull = bias_fast > bias_slow and adx_ok
        bias_bear = bias_fast < bias_slow and adx_ok

        # ── 15M indicator calculations ────────────────────────────────────────
        entry_price_arr = _apply_price(opens_15m, highs_15m, lows_15m, closes_15m, entry_price)
        ema_fast_15m = _apply_ma(entry_price_arr, entry_fast_p, entry_fast_m)
        sma_slow_15m = _apply_ma(entry_price_arr, entry_slow_p, entry_slow_m)
        sma_exit_15m = _apply_ma(entry_price_arr, exit_sma_p, "SMA")

        entry_fast      = ema_fast_15m[-2]
        entry_slow      = sma_slow_15m[-2]
        close_15m_last  = closes_15m[-2]   # most recent closed candle
        close_15m_prev  = closes_15m[-3]   # candle before the last closed one
        close_15m_prev2 = closes_15m[-4]   # candle before that

        # ── Entry triggers ────────────────────────────────────────────────────
        if require_confirm:
            # YOUR LOGIC:
            # For BUY:  previous candle close > candle before it (higher close = upward momentum)
            # For SELL: previous candle close < candle before it (lower close = downward momentum)
            # The current forming candle is ignored completely
            # 4H bias must still agree
            buy_trigger  = (entry_fast > entry_slow) and (close_15m_prev > close_15m_prev2)
            sell_trigger = (entry_fast < entry_slow) and (close_15m_prev < close_15m_prev2)
        else:
            # Original EA logic — current closed candle must be above/below fast MA
            price_above_fast = close_15m_last > entry_fast
            price_below_fast = close_15m_last < entry_fast
            buy_trigger  = (entry_fast > entry_slow) and price_above_fast
            sell_trigger = (entry_fast < entry_slow) and price_below_fast

        # ── Timeframe labels for display ──────────────────────────────────────
        tf_labels = {
            60: "1M", 300: "5M", 600: "10M", 900: "15M",
            1800: "30M", 3600: "1H", 7200: "2H", 14400: "4H",
            28800: "8H", 86400: "1D",
        }
        bias_tf_label  = tf_labels.get(bias_tf, f"{bias_tf}s")
        entry_tf_label = tf_labels.get(entry_tf, f"{entry_tf}s")

        # ── Final signal ─────────────────────────────────────────────────────
        if bias_bull and buy_trigger:
            signal = "BUY"
            if require_confirm:
                conf_note = f"Prev close ({close_15m_prev:.5f}) > prev-prev ({close_15m_prev2:.5f}) — higher close ✓"
            else:
                conf_note = f"Current close ({close_15m_last:.5f}) above {entry_fast_m}{entry_fast_p}"
            reasons = [
                f"{bias_tf_label} {bias_method}{bias_fast_p} > {bias_method}{bias_slow_p} — BULLISH",
                f"ADX({adx_4h:.1f}) >= {adx_threshold}" if adx_enabled else "ADX filter disabled",
                f"{entry_tf_label} {entry_fast_m}{entry_fast_p} > {entry_slow_m}{entry_slow_p}",
                conf_note,
            ]
            confidence = self._calc_confidence(adx_4h, bias_fast, bias_slow, entry_fast, entry_slow, adx_threshold)
            trend = "BULLISH"

        elif bias_bear and sell_trigger:
            signal = "SELL"
            if require_confirm:
                conf_note = f"Prev close ({close_15m_prev:.5f}) < prev-prev ({close_15m_prev2:.5f}) — lower close ✓"
            else:
                conf_note = f"Current close ({close_15m_last:.5f}) below {entry_fast_m}{entry_fast_p}"
            reasons = [
                f"{bias_tf_label} {bias_method}{bias_fast_p} < {bias_method}{bias_slow_p} — BEARISH",
                f"ADX({adx_4h:.1f}) >= {adx_threshold}" if adx_enabled else "ADX filter disabled",
                f"{entry_tf_label} {entry_fast_m}{entry_fast_p} < {entry_slow_m}{entry_slow_p}",
                conf_note,
            ]
            confidence = self._calc_confidence(adx_4h, bias_slow, bias_fast, entry_slow, entry_fast, adx_threshold)
            trend = "BEARISH"

        else:
            reasons = []
            if not adx_ok:
                reasons.append(f"ADX({adx_4h:.1f}) < {adx_threshold} — trend too weak")
            if not bias_bull and not bias_bear:
                reasons.append(f"{bias_tf_label} MAs too close — no clear bias")
            if bias_bull and not buy_trigger:
                if require_confirm:
                    reasons.append(
                        f"4H bullish but prev candle close ({close_15m_prev:.5f}) "
                        f"not higher than prev-prev ({close_15m_prev2:.5f})"
                    )
                else:
                    reasons.append(f"{bias_tf_label} bullish but {entry_tf_label} entry not confirmed")
            if bias_bear and not sell_trigger:
                if require_confirm:
                    reasons.append(
                        f"4H bearish but prev candle close ({close_15m_prev:.5f}) "
                        f"not lower than prev-prev ({close_15m_prev2:.5f})"
                    )
                else:
                    reasons.append(f"{bias_tf_label} bearish but {entry_tf_label} entry not confirmed")
            if not reasons:
                reasons.append("Timeframes do not align — waiting")
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

        # ── Emergency exit note (SMA50 only — matches EA logic) ─────────────
        pattern = None
        if exit_enabled:
            if signal == "BUY" or (signal == "WAIT" and bias_bull):
                if close_15m_last < sma_exit_15m[-2]:
                    pattern = f"Emergency Exit: Close < SMA{exit_sma_p}"
            elif signal == "SELL" or (signal == "WAIT" and bias_bear):
                if close_15m_last > sma_exit_15m[-2]:
                    pattern = f"Emergency Exit: Close > SMA{exit_sma_p}"

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
        adx_threshold: float = 20.0,
    ) -> float:
        bias_sep = abs(fast_bias - slow_bias) / slow_bias if slow_bias != 0 else 0
        bias_score = min(bias_sep * 100, 0.4)
        adx_score = min((adx - adx_threshold) / 50.0, 0.4)
        adx_score = max(adx_score, 0.0)
        entry_sep = abs(fast_entry - slow_entry) / slow_entry if slow_entry != 0 else 0
        entry_score = min(entry_sep * 100, 0.2)
        return min(round(bias_score + adx_score + entry_score, 3), 1.0)

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
