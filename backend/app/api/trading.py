"""
Trading control and execution routes.

POST   /api/v1/trading/start           — start the bot
POST   /api/v1/trading/pause           — pause the bot
POST   /api/v1/trading/resume          — resume the bot
POST   /api/v1/trading/stop            — stop the bot
GET    /api/v1/trading/status          — get bot status
POST   /api/v1/trading/trade           — place a manual trade
DELETE /api/v1/trading/trade/{id}      — close an open trade manually
GET    /api/v1/trading/trades          — list trades (with pagination)
GET    /api/v1/trading/trades/open     — list open trades
GET    /api/v1/trading/trades/{id}     — get a single trade
GET    /api/v1/trading/summary         — daily trade summary
GET    /api/v1/trading/balance         — live account balance from Deriv
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.crud.trade import get_open_trades, get_trade_by_id, get_trade_history, get_daily_summary
from app.models.user import User
from app.schemas.trade import TradeCreate, TradeResponse, TradeSummary
from app.services import trading_engine
from app.services.trading_engine import BotStatus
from app.db.session import async_session_factory
from app.core.logging import get_logger

router = APIRouter(prefix="/trading", tags=["Trading"])
logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Bot control
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/start")
async def start_bot(
    current_user: User = Depends(get_current_active_user),
):
    """Start the automated trading bot for the current user."""
    if not current_user.deriv_api_token:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="No Deriv API token saved. Add your token first via PUT /auth/token",
        )
    new_status = await trading_engine.start_trading(current_user, async_session_factory)
    logger.info("trading.start_requested", user_id=current_user.id, status=new_status)
    return {"status": new_status, "message": "Trading bot started"}


@router.post("/pause")
async def pause_bot(current_user: User = Depends(get_current_active_user)):
    """Pause the bot — keeps the connection alive but stops opening new trades."""
    new_status = await trading_engine.pause_trading(current_user.id)
    return {"status": new_status}


@router.post("/resume")
async def resume_bot(current_user: User = Depends(get_current_active_user)):
    """Resume a paused bot."""
    new_status = await trading_engine.resume_trading(current_user.id)
    return {"status": new_status}


@router.post("/stop")
async def stop_bot(current_user: User = Depends(get_current_active_user)):
    """Stop the bot and disconnect from Deriv."""
    new_status = await trading_engine.stop_trading(current_user.id)
    logger.info("trading.stop_requested", user_id=current_user.id)
    return {"status": new_status, "message": "Trading bot stopped"}


@router.get("/status")
async def get_bot_status(current_user: User = Depends(get_current_active_user)):
    """Return the current bot status."""
    bot_status = trading_engine.get_bot_status(current_user.id)
    return {"status": bot_status}


# ─────────────────────────────────────────────────────────────────────────────
# Account
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/balance")
async def get_balance(current_user: User = Depends(get_current_active_user)):
    """
    Fetch the live account balance directly from Deriv.
    Requires an active trading session (call /trading/start first).
    """
    session = trading_engine.get_session(current_user.id)
    if session is None or session.client is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="No active trading session. Call POST /trading/start first.",
        )
    balance = await session.client.get_balance()
    return balance


# ─────────────────────────────────────────────────────────────────────────────
# Trade execution
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/trade", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def place_trade(
    data: TradeCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Place a manual trade."""
    try:
        trade = await trading_engine.execute_trade(
            user=current_user,
            symbol=data.symbol,
            contract_type=data.contract_type,
            stake=data.stake,
            duration=data.duration,
            duration_unit=data.duration_unit,
            db=db,
            source="manual",
        )
    except RuntimeError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return trade


@router.delete("/trade/{trade_id}", response_model=TradeResponse)
async def close_trade(
    trade_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually close / sell an open trade before it expires."""
    trade = await get_trade_by_id(db, trade_id, current_user.id)
    if not trade:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Trade not found")
    if trade.status != "open":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Trade is not open")

    try:
        updated = await trading_engine.close_trade_manually(trade, current_user, db)
    except RuntimeError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return updated


# ─────────────────────────────────────────────────────────────────────────────
# Trade queries
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/trades/open", response_model=List[TradeResponse])
async def list_open_trades(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all currently open trades."""
    return await get_open_trades(db, current_user.id)


@router.get("/trades", response_model=List[TradeResponse])
async def list_trades(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated trade history (most recent first)."""
    return await get_trade_history(db, current_user.id, limit=limit, offset=offset)


@router.get("/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return details of a single trade."""
    trade = await get_trade_by_id(db, trade_id, current_user.id)
    if not trade:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Trade not found")
    return trade


@router.get("/summary", response_model=TradeSummary)
async def trade_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregated trading statistics."""
    from sqlalchemy import func, select
    from app.models.trade import Trade

    # Overall stats
    result = await db.execute(
        select(
            func.count(Trade.id).label("total"),
            func.coalesce(func.sum(Trade.profit), 0).label("total_profit"),
            func.count(Trade.id).filter(Trade.is_win == True).label("wins"),  # noqa: E712
        ).where(Trade.user_id == current_user.id, Trade.status == "closed")
    )
    row = result.one()
    total = row.total or 0
    wins = row.wins or 0

    open_count = len(await get_open_trades(db, current_user.id))
    daily = await get_daily_summary(db, current_user.id)

    return TradeSummary(
        total_trades=total,
        open_trades=open_count,
        closed_trades=total,
        total_profit=float(row.total_profit or 0),
        win_rate=(wins / total * 100) if total > 0 else 0.0,
        loss_rate=((total - wins) / total * 100) if total > 0 else 0.0,
        today_profit=daily["today_profit"],
        today_trades=daily["today_trades"],
    )
