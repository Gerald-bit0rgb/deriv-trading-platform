"""
AI Trading Signal Engine — 1-Minute Microtrading Strategy

Strategy logic:

  TREND DIRECTION filter (configurable, e.g. 4H EMA 5 vs EMA 13):
    Gates entries — BUY only allowed when the higher-timeframe trend is
    BULLISH (fast MA above slow MA); SELL only allowed when BEARISH.
    Can be disabled via require_trend_alignment=False.

  ENTRY signals (1M, must also match the trend direction above):
    BUY signal — all 3 must be true simultaneously:
      1. EMA 3 crosses ABOVE BB middle band (18-period SMA)
      2. MACD Histogram value > 0
      3. RSI 14 > 50

    SELL signal — all 3 must be true simultaneously:
      1. EMA 3 crosses BELOW BB middle band
      2. MACD Histogram value < 0
      3. RSI 14 < 50

  EXIT signals (crossback):
    BUY trade closes when:
      - EMA 3 crosses BELOW BB middle band (bearish crossback)

    SELL trade closes when:
      - EMA 3 crosses ABOVE BB middle band (bullish crossback)

  NO duration-based exits — trades stay open until crossback exit signal
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
    signal: str                       # BUY | SELL | WAIT | EXIT
    confidence: float                 # 0.0 – 1.0
    reason: str
    ema3_value: Optional[float] = None
    bb_middle: Optional[float] = None
    macd_histogram: Optional[float] = None
    rsi_value: Optional[float] = None
    volatility: str = "MEDIUM"
    trend_direction: Optional[str] = None    # BULLISH | BEARISH | NEUTRAL | None
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
        return np.array([np.mean(prices[:i + 1]) if i >= 0 else prices[0] for i in range(len(prices))])
    result = np.full_like(prices, np.nan, dtype=float)
    for i in range(period - 1, len(prices)):
        result[i] = np.mean(prices[i - period + 1: i + 1])
    return result


def _wma(prices: np.ndarray, period: int) -> np.ndarray:
    """Linearly Weighted Moving Average — most recent bar weighted highest."""
    weights = np.arange(1, period + 1, dtype=float)
    result = np.full_like(prices, np.nan, dtype=float)
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1: i + 1]
        result[i] = np.dot(window, weights) / weights.sum()
    return result


def _smma(prices: np.ndarray, period: int) -> np.ndarray:
    """Smoothed Moving Average (Wilder's) — same style as RSI's smoothing."""
    result = np.full_like(prices, np.nan, dtype=float)
    if len(prices) < period:
        return result
    result[period - 1] = np.mean(prices[:period])
    for i in range(period, len(prices)):
        result[i] = (result[i - 1] * (period - 1) + prices[i]) / period
    return result


def _ma(prices: np.ndarray, period: int, method: str = "EMA") -> np.ndarray:
    """Dispatch to the requested moving-average method (EMA, SMA, WMA, SMMA)."""
    method = (method or "EMA").upper()
    if method == "SMA":
        return _sma(prices, period)
    if method == "WMA":
        return _wma(prices, period)
    if method == "SMMA":
        return _smma(prices, period)
    return _ema(prices, period)


def _apply_price(
    opens: np.ndarray, highs: np.ndarray, lows: np.ndarray,
    closes: np.ndarray, applied_price: str,
) -> np.ndarray:
    """Select the price series an indicator should be calculated on."""
    p = (applied_price or "CLOSE").upper()
    if p == "OPEN":
        return opens
    if p == "HIGH":
        return highs
    if p == "LOW":
        return lows
    if p == "MEDIAN":
        return (highs + lows) / 2.0
    if p == "TYPICAL":
        return (highs + lows + closes) / 3.0
    if p == "WEIGHTED":
        return (highs + lows + closes + closes) / 4.0
    return closes


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
    seed = deltas[:period + 1]

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


# ────────────────────────────────────────────────────────────────────────��───
# 1-Minute Microtrading AI Engine
# ────────────────────────────────────────────────────────────────────────────

class AIEngine:
    """
    1-Minute Microtrading strategy — fully configurable parameters.
    Indicators: EMA 3, Bollinger Bands 18, MACD (9, 12, 26), RSI 14
    Exit: Crossback (EMA crosses back through BB middle)
    """

    def __init__(self, client: DerivClient, settings=None):
        self.client = client
        self._s = settings

    def _get(self, attr: str, default):
        if self._s is not None:
            return getattr(self._s, attr, default)
        return default

    async def _get_trend_direction(self, symbol: str) -> Optional[str]:
        """
        Higher-timeframe trend filter (e.g. 4H EMA 5 vs EMA 13).

        Returns "BULLISH" if the fast MA is above the slow MA, "BEARISH" if
        below, or None if candles couldn't be fetched (caller should treat
        that as "unknown" rather than blocking trades on a data hiccup).
        """
        timeframe = self._get("trend_timeframe", 14400)
        fast_period = self._get("trend_fast_period", 5)
        slow_period = self._get("trend_slow_period", 13)
        method = self._get("trend_ma_method", "EMA")
        applied_price = self._get("trend_applied_price", "CLOSE")

        try:
            candles = await self.client.get_candles(
                symbol, granularity=timeframe, count=max(slow_period + 10, 60)
            )
        except Exception as e:
            logger.warning("ai_engine.trend_fetch_failed", symbol=symbol, error=str(e))
            return None

        if len(candles) < slow_period + 2:
            return None

        opens = np.array([float(c["open"]) for c in candles])
        highs = np.array([float(c["high"]) for c in candles])
        lows = np.array([float(c["low"]) for c in candles])
        closes = np.array([float(c["close"]) for c in candles])
        prices = _apply_price(opens, highs, lows, closes, applied_price)

        fast_ma = _ma(prices, fast_period, method)
        slow_ma = _ma(prices, slow_period, method)

        fast_now = fast_ma[-2]
        slow_now = slow_ma[-2]
        if np.isnan(fast_now) or np.isnan(slow_now):
            return None

        if fast_now > slow_now:
            return "BULLISH"
        if fast_now < slow_now:
            return "BEARISH"
        return "NEUTRAL"

    async def analyse(self, symbol: str, granularity: Optional[int] = None) -> Signal:
        """Full 1M microtrading analysis — entry and exit signals.

        granularity: optional override of the saved entry_timeframe setting,
        useful for one-off API testing without changing the user's config.
        """

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

        require_trend = self._get("require_trend_alignment", True)
        entry_timeframe = granularity if granularity is not None else self._get("entry_timeframe", 60)

        # ── Fetch entry-timeframe candles + higher-timeframe trend, concurrently ─
        try:
            if require_trend:
                candles, trend_direction = await asyncio.gather(
                    self.client.get_candles(symbol, granularity=entry_timeframe, count=100),
                    self._get_trend_direction(symbol),
                )
            else:
                candles = await self.client.get_candles(
                    symbol, granularity=entry_timeframe, count=100
                )
                trend_direction = None
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
        ema_prices = _apply_price(opens, highs, lows, closes, ema_price)

        # ── Calculate indicators ───────────────────────────────────────────────
        ema3 = _ema(ema_prices, ema_period)
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

        # ── Trend direction gate ────────────────────────────────────────────────
        trend_bullish = (not require_trend) or (trend_direction == "BULLISH")
        trend_bearish = (not require_trend) or (trend_direction == "BEARISH")

        signal = "WAIT"
        confidence = 0.0
        reason_parts = []

        if bullish_cross and macd_positive and rsi_high and trend_bullish:
            signal = "BUY"
            reason_parts = [
                f"EMA({ema_period}) crossed above BB({bb_period}) middle",
                f"MACD histogram > 0 ({macd_hist_now:.6f})",
                f"RSI({rsi_period}) > 50 ({rsi_now:.1f})",
            ]
            if require_trend:
                reason_parts.append("4H trend BULLISH (aligned)")
            confidence = self._calc_confidence(
                bullish_cross, macd_positive, rsi_high, trend_bullish if require_trend else None
            )

        elif bearish_cross and macd_negative and rsi_low and trend_bearish:
            signal = "SELL"
            reason_parts = [
                f"EMA({ema_period}) crossed below BB({bb_period}) middle",
                f"MACD histogram < 0 ({macd_hist_now:.6f})",
                f"RSI({rsi_period}) < 50 ({rsi_now:.1f})",
            ]
            if require_trend:
                reason_parts.append("4H trend BEARISH (aligned)")
            confidence = self._calc_confidence(
                bearish_cross, macd_negative, rsi_low, trend_bearish if require_trend else None
            )

        else:
            # WAIT — diagnose why
            if require_trend and bullish_cross and macd_positive and rsi_high and not trend_bullish:
                reason_parts.append(
                    f"1M BUY conditions met but 4H trend is {trend_direction or 'unavailable'} (needs BULLISH)"
                )
            elif require_trend and bearish_cross and macd_negative and rsi_low and not trend_bearish:
                reason_parts.append(
                    f"1M SELL conditions met but 4H trend is {trend_direction or 'unavailable'} (needs BEARISH)"
                )
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
            trend_direction=trend_direction,
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
            trend_direction=trend_direction,
        )

    async def check_exit_signal(self, symbol: str, trade_type: str, granularity: int = 60) -> bool:
        """
        Check if an open trade should be exited based on crossback signal.

        Args:
            symbol: Trading symbol
            trade_type: "BUY" or "SELL"
            granularity: Timeframe in seconds (60 = 1M)

        Returns:
            True if exit signal is triggered, False otherwise

        Exit rules:
          - BUY trade closes when EMA crosses BELOW BB middle (bearish crossback)
          - SELL trade closes when EMA crosses ABOVE BB middle (bullish crossback)
        """
        try:
            ema_period = self._get("ema_fast_period", 3)
            bb_period = self._get("bb_period", 18)
            bb_std_dev = self._get("bb_std_dev", 2.0)
            bb_method = self._get("bb_method", "SMA")

            candles = await self.client.get_candles(symbol, granularity=granularity, count=50)
            if len(candles) < bb_period + 3:
                return False

            closes = np.array([float(c["close"]) for c in candles])
            ema3 = _ema(closes, ema_period)
            _, bb_middle, _ = _bb_bands(closes, bb_period, bb_std_dev, bb_method)

            # Current and previous bar
            ema3_now = ema3[-2]
            ema3_prev = ema3[-3] if len(ema3) >= 3 else ema3[-2]

            bb_mid_now = bb_middle[-2] if not np.isnan(bb_middle[-2]) else closes[-2]
            bb_mid_prev = bb_middle[-3] if len(bb_middle) >= 3 and not np.isnan(bb_middle[-3]) else bb_mid_now

            ema_above_bb_now = ema3_now > bb_mid_now
            ema_above_bb_prev = ema3_prev > bb_mid_prev

            # ── Exit logic ────────────────────────────────────────────────────
            if trade_type == "BUY":
                # BUY closes when EMA crosses BELOW BB middle (bearish crossback)
                bearish_cross = ema_above_bb_prev and (not ema_above_bb_now)
                if bearish_cross:
                    logger.info(
                        "ai_engine.exit_signal",
                        symbol=symbol,
                        trade_type=trade_type,
                        reason="EMA crossed below BB middle (bearish crossback)",
                    )
                    return True

            elif trade_type == "SELL":
                # SELL closes when EMA crosses ABOVE BB middle (bullish crossback)
                bullish_cross = (not ema_above_bb_prev) and ema_above_bb_now
                if bullish_cross:
                    logger.info(
                        "ai_engine.exit_signal",
                        symbol=symbol,
                        trade_type=trade_type,
                        reason="EMA crossed above BB middle (bullish crossback)",
                    )
                    return True

            return False

        except Exception as e:
            logger.error(
                "ai_engine.exit_check_failed",
                symbol=symbol,
                trade_type=trade_type,
                error=str(e),
            )
            return False

    def _calc_confidence(
        self, crossover: bool, macd_ok: bool, rsi_ok: bool, trend_ok: Optional[bool] = None
    ) -> float:
        """
        Confidence score (0-1).

        With trend gating enabled (trend_ok is not None), all 4 conditions
        contribute; without it, just the 3 original 1M conditions.
        """
        if trend_ok is None:
            score = 0.0
            if crossover:
                score += 0.4
            if macd_ok:
                score += 0.3
            if rsi_ok:
                score += 0.3
            return min(round(score, 3), 1.0)

        score = 0.0
        if crossover:
            score += 0.3
        if macd_ok:
            score += 0.2
        if rsi_ok:
            score += 0.2
        if trend_ok:
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

    async def get_atr_value(
        self, symbol: str, period: int = 14, granularity: int = 60
    ) -> Optional[float]:
        """
        Current ATR (Average True Range) in price units, for computing
        ATR-based stop-loss / take-profit distances at trade entry.
        Returns None if candles can't be fetched.
        """
        try:
            candles = await self.client.get_candles(
                symbol, granularity=granularity, count=max(period + 10, 30)
            )
            if len(candles) < 2:
                return None
            highs = np.array([float(c["high"]) for c in candles])
            lows = np.array([float(c["low"]) for c in candles])
            closes = np.array([float(c["close"]) for c in candles])
            return _atr(highs, lows, closes, period=period)
        except Exception as e:
            logger.warning("ai_engine.atr_fetch_failed", symbol=symbol, error=str(e))
            return None

    async def batch_analyse(
        self, symbols: List[str], granularity: Optional[int] = None
    ) -> Dict[str, Signal]:
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
