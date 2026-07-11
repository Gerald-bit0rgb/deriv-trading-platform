"""
AI signal routes.

GET  /api/v1/ai/signal/{symbol}       — get a trading signal for one symbol
POST /api/v1/ai/signal/batch          — signals for multiple symbols
GET  /api/v1/ai/analyse/{symbol}      — full technical analysis
POST /api/v1/ai/auto-trade/{symbol}   — let the AI decide and execute the trade
"""
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.ai import AISignalResponse, MarketAnalysis
from app.services import trading_engine
from app.services.ai_engine import AIEngine
from app.core.logging import get_logger

router = APIRouter(prefix="/ai", tags=["AI Engine"])
logger = get_logger(__name__)


def _get_ai_engine(user_id: int) -> AIEngine:
    """Retrieve the AI engine backed by the user's active Deriv client."""
    session = trading_engine.get_session(user_id)
    if session is None or session.client is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="No active trading session. Call POST /trading/start first.",
        )
    return AIEngine(client=session.client)


@router.get("/signal/{symbol}", response_model=AISignalResponse)
async def get_signal(
    symbol: str,
    granularity: int = Query(60, description="Candle granularity in seconds"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate a BUY / SELL / WAIT signal for *symbol*.

    Requires an active trading session.
    """
    engine = _get_ai_engine(current_user.id)
    signal = await engine.analyse(symbol, granularity=granularity)

    logger.info(
        "ai.signal_requested",
        user_id=current_user.id,
        symbol=symbol,
        signal=signal.signal,
        confidence=signal.confidence,
    )

    return AISignalResponse(
        symbol=signal.symbol,
        signal=signal.signal,
        confidence=signal.confidence,
        reason=signal.reason,
        trend=signal.trend,
        volatility=signal.volatility,
        pattern=signal.pattern,
        entry_price=signal.entry_price,
        suggested_stake=signal.suggested_stake,
        generated_at=signal.generated_at,
    )


@router.post("/signal/batch", response_model=List[AISignalResponse])
async def get_batch_signals(
    symbols: List[str] = Body(..., examples=[["R_100", "R_50", "frxEURUSD"]]),
    granularity: int = Query(60),
    current_user: User = Depends(get_current_active_user),
):
    """Get AI signals for multiple symbols at once."""
    if len(symbols) > 10:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 symbols per batch request",
        )
    engine = _get_ai_engine(current_user.id)
    results = await engine.batch_analyse(symbols, granularity=granularity)

    return [
        AISignalResponse(
            symbol=sig.symbol,
            signal=sig.signal,
            confidence=sig.confidence,
            reason=sig.reason,
            trend=sig.trend,
            volatility=sig.volatility,
            pattern=sig.pattern,
            entry_price=sig.entry_price,
            suggested_stake=sig.suggested_stake,
            generated_at=sig.generated_at,
        )
        for sig in results.values()
    ]


@router.post("/auto-trade/{symbol}", status_code=status.HTTP_201_CREATED)
async def ai_auto_trade(
    symbol: str,
    stake: float = Query(1.0, gt=0, description="Stake amount"),
    duration: int = Query(5, gt=0),
    duration_unit: str = Query("t", description="t=ticks, s=seconds, m=minutes"),
    granularity: int = Query(60),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ask the AI to analyse the market and automatically execute a trade
    if it produces a BUY or SELL signal above the confidence threshold.
    """
    engine = _get_ai_engine(current_user.id)
    signal = await engine.analyse(symbol, granularity=granularity)

    if signal.signal == "WAIT":
        return {
            "executed": False,
            "signal": signal.signal,
            "confidence": signal.confidence,
            "reason": signal.reason,
            "message": "AI decided to WAIT — no trade placed",
        }

    # Map signal direction to Deriv contract type
    contract_type = "CALL" if signal.signal == "BUY" else "PUT"

    try:
        trade = await trading_engine.execute_trade(
            user=current_user,
            symbol=symbol,
            contract_type=contract_type,
            stake=stake,
            duration=duration,
            duration_unit=duration_unit,
            db=db,
            ai_signal=signal.signal,
            ai_confidence=signal.confidence,
            ai_reason=signal.reason,
            source="ai",
        )
        return {
            "executed": True,
            "trade_id": trade.id,
            "signal": signal.signal,
            "confidence": signal.confidence,
            "reason": signal.reason,
            "contract_type": contract_type,
        }
    except RuntimeError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
