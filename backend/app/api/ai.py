"""
AI signal routes.

GET  /api/v1/ai/signal/{symbol}       — get a trading signal for one symbol
POST /api/v1/ai/signal/batch          — signals for multiple symbols
POST /api/v1/ai/auto-trade/{symbol}   — let the AI decide and execute the trade
"""
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.crud.strategy import get_strategy_settings
from app.models.user import User
from app.schemas.ai import AISignalResponse
from app.services import trading_engine
from app.services.ai_engine import AIEngine
from app.core.logging import get_logger

router = APIRouter(prefix="/ai", tags=["AI Engine"])
logger = get_logger(__name__)


async def _get_engine(user_id: int, db: AsyncSession) -> AIEngine:
    """Get AI engine — auto-restarts session if expired."""
    from app.db.session import async_session_factory
    from app.crud.user import get_user_by_id

    session = trading_engine.get_session(user_id)
    if session is None or session.client is None:
        # Try to restart from DB
        user = await get_user_by_id(db, user_id)
        if user and user.deriv_api_token:
            try:
                await trading_engine.start_trading_with_token(
                    user_id=user.id,
                    api_token=user.deriv_api_token,
                    username=user.username,
                    fcm_token=user.fcm_token,
                    db_factory=async_session_factory,
                    symbol="R_100",
                    account_type="demo",
                )
                session = trading_engine.get_session(user_id)
            except Exception:
                pass

    if session is None or session.client is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="No active trading session. Call POST /trading/start first.",
        )
    strat = await get_strategy_settings(db, user_id)
    return AIEngine(client=session.client, settings=strat)


@router.get("/signal/{symbol}", response_model=AISignalResponse)
async def get_signal(
    symbol: str,
    granularity: int = Query(60, description="Candle granularity in seconds"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a BUY / SELL / WAIT signal using your configured strategy settings."""
    engine = await _get_engine(current_user.id, db)
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
        ema3_value=signal.ema3_value,
        bb_middle=signal.bb_middle,
        macd_histogram=signal.macd_histogram,
        rsi_value=signal.rsi_value,
        volatility=signal.volatility,
        trend_direction=signal.trend_direction,
        generated_at=signal.generated_at,
    )


@router.post("/signal/batch", response_model=List[AISignalResponse])
async def get_batch_signals(
    symbols: List[str] = Body(..., examples=[["R_100", "R_50", "frxEURUSD"]]),
    granularity: int = Query(60),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get signals for up to 10 symbols at once using your strategy settings."""
    if len(symbols) > 10:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 symbols per batch request",
        )
    engine = await _get_engine(current_user.id, db)
    results = await engine.batch_analyse(symbols, granularity=granularity)

    return [
        AISignalResponse(
            symbol=sig.symbol,
            signal=sig.signal,
            confidence=sig.confidence,
            reason=sig.reason,
            ema3_value=sig.ema3_value,
            bb_middle=sig.bb_middle,
            macd_histogram=sig.macd_histogram,
            rsi_value=sig.rsi_value,
            volatility=sig.volatility,
            trend_direction=sig.trend_direction,
            generated_at=sig.generated_at,
        )
        for sig in results.values()
    ]


@router.post("/auto-trade/{symbol}", status_code=status.HTTP_201_CREATED)
async def ai_auto_trade(
    symbol: str,
    lot_size: float = Query(0.01, gt=0, description="Lot size, e.g. 0.01, 0.1, 1.0"),
    granularity: int = Query(60),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyse market and execute a trade if confident enough.
    Auto-restarts the bot session if it has expired."""
    from app.db.session import async_session_factory

    # ── Auto-restart bot session if expired ───────────────────────────────────
    session = trading_engine.get_session(current_user.id)
    if session is None or session.client is None:
        if not current_user.deriv_api_token:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="No Deriv API token saved. Go to Profile and save your token first.",
            )
        try:
            await trading_engine.start_trading_with_token(
                user_id=current_user.id,
                api_token=current_user.deriv_api_token,
                username=current_user.username,
                fcm_token=current_user.fcm_token,
                db_factory=async_session_factory,
                symbol=symbol,
                account_type="demo",
            )
            logger.info("ai_auto_trade.session_restarted", user_id=current_user.id)
        except Exception as e:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not connect to Deriv: {str(e)}",
            )

    engine = await _get_engine(current_user.id, db)
    signal = await engine.analyse(symbol, granularity=granularity)

    if signal.signal == "WAIT":
        return {
            "executed": False,
            "signal": signal.signal,
            "confidence": signal.confidence,
            "reason": signal.reason,
            "message": "AI decided to WAIT — no trade placed",
        }

    contract_type = "MULTUP" if signal.signal == "BUY" else "MULTDOWN"

    try:
        trade = await trading_engine.execute_trade(
            user=current_user,
            symbol=symbol,
            contract_type=contract_type,
            lot_size=lot_size,
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
