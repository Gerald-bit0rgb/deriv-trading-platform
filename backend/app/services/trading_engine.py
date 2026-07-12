"""
Trading Engine — the core automation layer.

Responsibilities:
  - Maintain one DerivClient per active user session
  - Start / pause / resume / stop automated trading
  - Execute trades based on AI signals or manual requests
  - Monitor open positions and close them when TP/SL is hit
  - Enforce risk-management rules before every trade
  - Persist every trade action to the database
  - Emit notifications on key events
"""
import asyncio
from enum import Enum
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud import trade as trade_crud
from app.crud import notification as notif_crud
from app.crud.risk import get_or_create_risk_settings
from app.models.trade import Trade
from app.models.user import User
from app.services.deriv_client import DerivClient
from app.services.notification_service import send_push_notification

logger = get_logger(__name__)


class BotStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class UserSession:
    """
    Holds everything that belongs to one logged-in user's trading session.
    Uses plain values instead of ORM objects to avoid DetachedInstanceError.
    """

    def __init__(
        self,
        user_id: int,
        api_token: str,
        username: str,
        fcm_token: Optional[str],
        db_factory,
    ):
        self.user_id = user_id
        self.api_token = api_token
        self.username = username
        self.fcm_token = fcm_token
        self.db_factory = db_factory
        self.client: Optional[DerivClient] = None
        self.status: BotStatus = BotStatus.STOPPED
        self.monitor_task: Optional[asyncio.Task] = None
        self._tick_sub_ids: Dict[str, str] = {}
        self._latest_prices: Dict[str, float] = {}

    async def connect(self) -> None:
        """Create a DerivClient and authorise it."""
        self.client = DerivClient(api_token=self.api_token)
        await self.client.connect()
        logger.info("session.connected", user_id=self.user_id)

    async def disconnect(self) -> None:
        if self.client:
            await self.client.unsubscribe_all()
            await self.client.disconnect()
        logger.info("session.disconnected", user_id=self.user_id)


# ─────────────────────────────────────────────────────────────────────────────
# Global session registry  (user_id → UserSession)
# ─────────────────────────────────────────────────────────────────────────────
_sessions: Dict[int, UserSession] = {}


def get_session(user_id: int) -> Optional[UserSession]:
    return _sessions.get(user_id)


# ─────────────────────────────────────────────────────────────────────────────
# Engine control functions
# ─────────────────────────────────────────────────────────────────────────────

async def start_trading_with_token(
    user_id: int,
    api_token: str,
    username: str,
    fcm_token: Optional[str],
    db_factory,
) -> str:
    """
    Connect to Deriv and start the automated trading bot.
    Uses plain values to avoid SQLAlchemy DetachedInstanceError.
    """
    session = _sessions.get(user_id)

    if session is None:
        session = UserSession(
            user_id=user_id,
            api_token=api_token,
            username=username,
            fcm_token=fcm_token,
            db_factory=db_factory,
        )
        _sessions[user_id] = session

    if session.status == BotStatus.RUNNING:
        return BotStatus.RUNNING

    await session.connect()
    session.status = BotStatus.RUNNING

    session.monitor_task = asyncio.create_task(
        _monitor_loop(session), name=f"monitor-{user_id}"
    )

    logger.info("trading_engine.started", user_id=user_id)
    return BotStatus.RUNNING


async def start_trading(user: User, db_factory) -> str:
    """Legacy wrapper — kept for compatibility."""
    return await start_trading_with_token(
        user_id=user.id,
        api_token=user.deriv_api_token or "",
        username=user.username,
        fcm_token=user.fcm_token,
        db_factory=db_factory,
    )


async def pause_trading(user_id: int) -> str:
    session = _sessions.get(user_id)
    if session and session.status == BotStatus.RUNNING:
        session.status = BotStatus.PAUSED
        logger.info("trading_engine.paused", user_id=user_id)
    return session.status if session else BotStatus.STOPPED


async def resume_trading(user_id: int) -> str:
    session = _sessions.get(user_id)
    if session and session.status == BotStatus.PAUSED:
        session.status = BotStatus.RUNNING
        logger.info("trading_engine.resumed", user_id=user_id)
    return session.status if session else BotStatus.STOPPED


async def stop_trading(user_id: int) -> str:
    session = _sessions.get(user_id)
    if session:
        session.status = BotStatus.STOPPED
        if session.monitor_task:
            session.monitor_task.cancel()
        await session.disconnect()
        _sessions.pop(user_id, None)
        logger.info("trading_engine.stopped", user_id=user_id)
    return BotStatus.STOPPED


def get_bot_status(user_id: int) -> str:
    session = _sessions.get(user_id)
    return session.status if session else BotStatus.STOPPED


# ─────────────────────────────────────────────────────────────────────────────
# Trade execution
# ─────────────────────────────────────────────────────────────────────────────

async def execute_trade(
    user: User,
    symbol: str,
    contract_type: str,
    stake: float,
    duration: int,
    duration_unit: str,
    db: AsyncSession,
    ai_signal: Optional[str] = None,
    ai_confidence: Optional[float] = None,
    ai_reason: Optional[str] = None,
    source: str = "manual",
) -> Trade:
    """
    Validate risk rules, place the contract on Deriv, and record the trade.
    """
    # ── 1. Risk checks ────────────────────────────────────────────────────────
    risk = await get_or_create_risk_settings(db, user.id)

    if risk.emergency_stop:
        raise RuntimeError("Emergency stop is active — trading halted")

    if not risk.trading_enabled:
        raise RuntimeError("Trading is disabled in risk settings")

    if stake > risk.max_stake:
        raise RuntimeError(f"Stake {stake} exceeds max allowed {risk.max_stake}")

    # Check open-trade count
    open_trades = await trade_crud.get_open_trades(db, user.id)
    if len(open_trades) >= risk.max_open_trades:
        raise RuntimeError(
            f"Max open trades ({risk.max_open_trades}) already reached"
        )

    # Check daily trade count
    summary = await trade_crud.get_daily_summary(db, user.id)
    if summary["today_trades"] >= risk.max_daily_trades:
        raise RuntimeError("Daily trade limit reached")

    # Check daily loss
    if summary["today_profit"] <= -abs(risk.max_daily_loss):
        raise RuntimeError("Daily loss limit reached — trading stopped for today")

    # Check AI confidence gate
    if ai_confidence is not None and ai_confidence < risk.min_ai_confidence:
        raise RuntimeError(
            f"AI confidence {ai_confidence:.2f} below minimum {risk.min_ai_confidence}"
        )

    # ── 2. Get active session / client ────────────────────────────────────────
    session = _sessions.get(user.id)
    if session is None or session.client is None:
        raise RuntimeError("Trading session not active — call /trading/start first")

    # ── 3. Place trade on Deriv ───────────────────────────────────────────────
    contract = await session.client.buy_contract(
        symbol=symbol,
        contract_type=contract_type,
        stake=stake,
        duration=duration,
        duration_unit=duration_unit,
    )

    # ── 4. Persist to database ────────────────────────────────────────────────
    trade = await trade_crud.create_trade(
        db,
        user_id=user.id,
        contract_id=str(contract.get("contract_id")),
        symbol=symbol,
        contract_type=contract_type,
        duration=duration,
        duration_unit=duration_unit,
        stake=stake,
        entry_price=contract.get("entry_spot"),
        payout=contract.get("payout"),
        ai_signal=ai_signal,
        ai_confidence=ai_confidence,
        ai_reason=ai_reason,
        source=source,
        status="open",
    )

    # ── 5. Send notification ──────────────────────────────────────────────────
    await notif_crud.create_notification(
        db,
        user_id=user.id,
        type_="trade_open",
        title="Trade Opened",
        body=f"{contract_type} on {symbol} | Stake: {stake}",
    )
    if user.fcm_token:
        asyncio.create_task(
            send_push_notification(
                token=user.fcm_token,
                title="Trade Opened",
                body=f"{contract_type} on {symbol} | Stake: {stake}",
            )
        )

    logger.info(
        "trade.executed",
        user_id=user.id,
        trade_id=trade.id,
        contract_id=trade.contract_id,
        symbol=symbol,
        contract_type=contract_type,
        stake=stake,
    )
    return trade


async def close_trade_manually(
    trade: Trade, user: User, db: AsyncSession
) -> Trade:
    """Manually sell / close an open trade before expiry."""
    session = _sessions.get(user.id)
    if session is None or session.client is None:
        raise RuntimeError("Trading session not active")

    sell_info = await session.client.sell_contract(int(trade.contract_id))
    sold_for = float(sell_info.get("sold_for", 0))
    profit = sold_for - trade.stake

    updated = await trade_crud.close_trade(
        db,
        trade=trade,
        exit_price=float(sell_info.get("exit_spot", 0)),
        profit=profit,
        payout=sold_for,
    )

    await _notify_trade_close_by_id(user.id, user.fcm_token, updated, db)
    return updated


# ─────────────────────────────────────────────────────────────────────────────
# Background position monitor
# ─────────────────────────────────────────────────────────────────────────────

async def _monitor_loop(session: UserSession) -> None:
    """
    Polls open positions every 5 seconds.

    - Checks Deriv for contract status
    - Closes finished contracts in the DB
    - Sends TP/SL notifications
    """
    logger.info("monitor.started", user_id=session.user_id)
    while session.status in (BotStatus.RUNNING, BotStatus.PAUSED):
        try:
            if session.status == BotStatus.RUNNING:
                async with session.db_factory() as db:
                    await _check_open_trades(session, db)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("monitor.error", user_id=session.user_id, error=str(e))
        await asyncio.sleep(5)
    logger.info("monitor.stopped", user_id=session.user_id)


async def _check_open_trades(session: UserSession, db: AsyncSession) -> None:
    """Sync local open trades with Deriv's actual state."""
    open_trades = await trade_crud.get_open_trades(db, session.user_id)
    if not open_trades:
        return

    for trade in open_trades:
        if not trade.contract_id:
            continue
        try:
            details = await session.client.get_contract_details(int(trade.contract_id))
            status = details.get("status")

            if status in ("won", "lost", "sold"):
                profit = float(details.get("profit", 0))
                payout = float(details.get("sell_price") or details.get("bid_price") or 0)
                exit_price = float(details.get("exit_tick") or details.get("sell_spot") or 0)

                await trade_crud.close_trade(
                    db,
                    trade=trade,
                    exit_price=exit_price,
                    profit=profit,
                    payout=payout,
                )
                await _notify_trade_close_by_id(
                    session.user_id, session.fcm_token, trade, db
                )
                await db.commit()
                logger.info(
                    "trade.auto_closed",
                    trade_id=trade.id,
                    status=status,
                    profit=profit,
                )
        except Exception as e:
            logger.warning("monitor.check_failed", trade_id=trade.id, error=str(e))


async def _notify_trade_close_by_id(
    user_id: int, fcm_token: Optional[str], trade: Trade, db: AsyncSession
) -> None:
    """Send DB notification + push notification when a trade closes."""
    result = "WIN" if trade.is_win else "LOSS"
    profit_val = trade.profit or 0
    profit_str = f"+{profit_val:.2f}" if trade.is_win else f"{profit_val:.2f}"
    body = f"{trade.contract_type} on {trade.symbol} | {result} {profit_str}"

    await notif_crud.create_notification(
        db,
        user_id=user_id,
        type_="trade_close",
        title=f"Trade Closed — {result}",
        body=body,
    )
    if fcm_token:
        asyncio.create_task(
            send_push_notification(
                token=fcm_token,
                title=f"Trade Closed — {result}",
                body=body,
            )
        )


async def _notify_trade_close(user: User, trade: Trade, db: AsyncSession) -> None:
    """Legacy wrapper for close notification."""
    await _notify_trade_close_by_id(user.id, user.fcm_token, trade, db)
