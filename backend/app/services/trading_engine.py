"""
Trading Engine — MA Bias Basket Strategy

Automated bot loop:
  Every new 15M bar:
    1. Run MA Bias Basket analysis (4H bias + 15M entry)
    2. If BUY/SELL signal and basket allows → place trade
    3. Check basket total profit → close all if >= InpBasketCloseUSD
    4. Emergency exit → close all if 15M candle closes against SMA50
  Every 5 seconds:
    5. Sync open trade statuses with Deriv

Settings (read from user's RiskSettings):
  default_stake       → lot size per entry
  max_open_trades     → max basket size
  daily_profit_target → basket close USD target
"""
import asyncio
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.crud import notification as notif_crud
from app.crud import trade as trade_crud
from app.crud.risk import get_or_create_risk_settings
from app.models.trade import Trade
from app.models.user import User
from app.services.deriv_client import DerivClient
from app.services.notification_service import send_push_notification

logger = get_logger(__name__)

# Default trading symbol for the automated bot
DEFAULT_SYMBOL = "R_100"   # Volatility 100 Index — 24/7 synthetic


class BotStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class UserSession:
    """All state for one user's trading session. Uses plain values only."""

    def __init__(
        self,
        user_id: int,
        api_token: str,
        username: str,
        fcm_token: Optional[str],
        db_factory,
        symbol: str = "R_100",
        account_type: str = "demo",
    ):
        self.user_id = user_id
        self.api_token = api_token
        self.username = username
        self.fcm_token = fcm_token
        self.db_factory = db_factory
        self.symbol = symbol
        self.account_type = account_type
        self.client: Optional[DerivClient] = None
        self.status: BotStatus = BotStatus.STOPPED
        self.monitor_task: Optional[asyncio.Task] = None
        self.strategy_task: Optional[asyncio.Task] = None
        self._last_bar_time: Optional[int] = None   # last 15M bar epoch processed

    async def connect(self) -> None:
        self.client = DerivClient(
            api_token=self.api_token,
            account_type=self.account_type,
        )
        await self.client.connect()
        logger.info("session.connected", user_id=self.user_id, account_type=self.account_type)

    async def disconnect(self) -> None:
        if self.client:
            await self.client.unsubscribe_all()
            await self.client.disconnect()
        logger.info("session.disconnected", user_id=self.user_id)


# ── Session registry ──────────────────────────────────────────────────────────
_sessions: Dict[int, UserSession] = {}


def get_session(user_id: int) -> Optional[UserSession]:
    return _sessions.get(user_id)


# ─────────────────────────────────────────────────────────────────────────────
# Engine control
# ─────────────────────────────────────────────────────────────────────────────

async def start_trading_with_token(
    user_id: int,
    api_token: str,
    username: str,
    fcm_token: Optional[str],
    db_factory,
    symbol: str = "R_100",
    account_type: str = "demo",
) -> str:
    session = _sessions.get(user_id)

    if session is None:
        session = UserSession(
            user_id=user_id,
            api_token=api_token,
            username=username,
            fcm_token=fcm_token,
            db_factory=db_factory,
            symbol=symbol,
            account_type=account_type,
        )
        _sessions[user_id] = session
    else:
        # Update symbol and account_type if bot restarts with new settings
        session.symbol = symbol
        session.account_type = account_type

    if session.status == BotStatus.RUNNING:
        return BotStatus.RUNNING

    await session.connect()
    session.status = BotStatus.RUNNING

    # Background task 1: sync trade statuses every 5 seconds
    session.monitor_task = asyncio.create_task(
        _monitor_loop(session), name=f"monitor-{user_id}"
    )

    # Background task 2: run MA Bias Basket strategy on every new 15M bar
    session.strategy_task = asyncio.create_task(
        _strategy_loop(session), name=f"strategy-{user_id}"
    )

    logger.info("trading_engine.started", user_id=user_id)
    return BotStatus.RUNNING


async def start_trading(user: User, db_factory) -> str:
    """Legacy wrapper."""
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
        if session.strategy_task:
            session.strategy_task.cancel()
        await session.disconnect()
        _sessions.pop(user_id, None)
        logger.info("trading_engine.stopped", user_id=user_id)
    return BotStatus.STOPPED


def get_bot_status(user_id: int) -> str:
    session = _sessions.get(user_id)
    return session.status if session else BotStatus.STOPPED


# ─────────────────────────────────────────────────────────────────────────────
# MA Bias Basket Strategy Loop
# ─────────────────────────────────────────────────────────────────────────────

async def _strategy_loop(session: UserSession) -> None:
    """
    Runs the MA Bias Basket strategy on every new 15M bar.
    Checks every 60 seconds for a new bar.
    """
    logger.info("strategy.started", user_id=session.user_id)

    while session.status in (BotStatus.RUNNING, BotStatus.PAUSED):
        try:
            if session.status == BotStatus.RUNNING:
                async with session.db_factory() as db:
                    await _run_basket_strategy(session, db)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("strategy.error", user_id=session.user_id, error=str(e))

        # Check every 60 seconds for a new 15M bar
        await asyncio.sleep(60)

    logger.info("strategy.stopped", user_id=session.user_id)


async def _run_basket_strategy(session: UserSession, db: AsyncSession) -> None:
    """
    MA Bias Basket strategy execution for one bar check.

    Steps:
      1. Check if a new 15M bar has formed
      2. Run AI engine analysis
      3. Check basket profit → close if target reached
      4. Emergency exit check (SMA50 only)
      5. Place new trade if signal aligns and basket allows
    """
    from app.services.ai_engine import AIEngine
    from app.crud.strategy import get_strategy_settings as get_strat

    if session.client is None:
        return

    # Load strategy settings for this user
    strat = await get_strat(db, session.user_id)
    engine = AIEngine(client=session.client, settings=strat)

    # ── Get risk settings ─────────────────────────────────────────────────────
    risk = await get_or_create_risk_settings(db, session.user_id)

    if risk.emergency_stop or not risk.trading_enabled:
        return

    # ── Check for new bar on entry timeframe ─────────────────────────────────
    try:
        candles = await session.client.get_candles(
            session.symbol, granularity=strat.entry_timeframe, count=5
        )
        if not candles:
            logger.warning("strategy.no_candles_returned",
                           user_id=session.user_id, symbol=session.symbol)
            return
        current_bar_epoch = int(candles[-2].get("epoch", 0))
        if current_bar_epoch == session._last_bar_time:
            logger.info("strategy.same_bar_skipping", user_id=session.user_id)
            return
        session._last_bar_time = current_bar_epoch
        logger.info("strategy.new_bar_processing",
                    user_id=session.user_id,
                    epoch=current_bar_epoch,
                    symbol=session.symbol)
    except Exception as e:
        logger.error("strategy.bar_check_failed",
                     user_id=session.user_id,
                     symbol=session.symbol,
                     error=str(e))
        return

    logger.info("strategy.new_bar", user_id=session.user_id, epoch=current_bar_epoch)

    # ── Get open trades ───────────────────────────────────────────────────────
    open_trades = await trade_crud.get_open_trades(db, session.user_id)
    basket_count = len(open_trades)

    # ── Step 1: Basket profit check → close all if target reached ─────────────
    if basket_count > 0:
        total_profit = await _get_basket_profit(session, open_trades)
        # Basket close target: max of $0.40 or 4x the default stake
        basket_close_usd = max(0.40, risk.default_stake * 4)

        if total_profit >= basket_close_usd:
            await _close_all_basket(session, open_trades, db)
            await _send_notif(
                session, db, "basket_close",
                "Basket Closed — Profit Target",
                f"Basket profit reached ${total_profit:.2f} — all trades closed",
            )
            logger.info(
                "strategy.basket_closed_profit",
                user_id=session.user_id,
                profit=total_profit,
            )
            return

    # ── Step 2: Run AI analysis ────────────────────────────────────────────────
    try:
        signal = await engine.analyse(session.symbol, granularity=60)
        logger.info(
            "strategy.analysis_result",
            user_id=session.user_id,
            symbol=session.symbol,
            signal=signal.signal,
            confidence=signal.confidence,
            reason=signal.reason[:100] if signal.reason else "",
        )
    except Exception as e:
        logger.error("strategy.analysis_failed", user_id=session.user_id, error=str(e))
        return

    logger.info(
        "strategy.signal",
        user_id=session.user_id,
        signal=signal.signal,
        confidence=signal.confidence,
        reason=signal.reason,
    )

    # ── Step 3: Emergency exit (SMA50 only) ────────────────────────────────────
    if basket_count > 0 and signal.pattern and "Emergency Exit" in signal.pattern:
        basket_dir = _get_basket_direction(open_trades)
        should_exit = (
            (basket_dir == "BUY" and signal.signal != "BUY") or
            (basket_dir == "SELL" and signal.signal != "SELL")
        )
        if should_exit:
            await _close_all_basket(session, open_trades, db)
            await _send_notif(
                session, db, "emergency_exit",
                "Emergency Exit",
                f"Basket closed — {signal.pattern}",
            )
            logger.info(
                "strategy.emergency_exit",
                user_id=session.user_id,
                pattern=signal.pattern,
            )
            return

    # ── Step 4: Entry check ────────────────────────────────────────────────────
    if signal.signal == "WAIT":
        return

    # Check confidence threshold
    if signal.confidence < risk.min_ai_confidence:
        logger.info(
            "strategy.confidence_too_low",
            confidence=signal.confidence,
            min=risk.min_ai_confidence,
        )
        return

    # Check basket size limit
    if basket_count >= risk.max_open_trades:
        logger.info("strategy.basket_full", count=basket_count)
        return

    # Check daily limits — no max_daily_trades check — bot trades until stopped
    summary = await trade_crud.get_daily_summary(db, session.user_id)
    if summary["today_profit"] <= -abs(risk.max_daily_loss):
        return

    # Don't add trades in opposite direction to existing basket
    if basket_count > 0:
        basket_dir = _get_basket_direction(open_trades)
        if basket_dir and basket_dir != signal.signal:
            logger.info(
                "strategy.opposite_direction_blocked",
                basket=basket_dir,
                signal=signal.signal,
            )
            return

    # ── Step 5: Place trade ───────────────────────────────────────────────────
    contract_type = "CALL" if signal.signal == "BUY" else "PUT"
    stake = risk.default_stake

    try:
        contract = await session.client.buy_contract(
            symbol=session.symbol,
            contract_type=contract_type,
            stake=stake,
            duration=strat.trade_duration,
            duration_unit=strat.trade_duration_unit,
        )

        trade = await trade_crud.create_trade(
            db,
            user_id=session.user_id,
            contract_id=str(contract.get("contract_id")),
            symbol=session.symbol,
            contract_type=contract_type,
            duration=strat.trade_duration,
            duration_unit=strat.trade_duration_unit,
            stake=stake,
            entry_price=contract.get("entry_spot"),
            payout=contract.get("payout"),
            ai_signal=signal.signal,
            ai_confidence=signal.confidence,
            ai_reason=signal.reason,
            source="auto",
            status="open",
        )
        await db.commit()

        await _send_notif(
            session, db, "trade_open",
            f"Auto Trade Opened — {signal.signal}",
            f"{contract_type} on {session.symbol} | Stake: ${stake} | "
            f"Confidence: {int(signal.confidence * 100)}%",
        )

        logger.info(
            "strategy.trade_placed",
            user_id=session.user_id,
            trade_id=trade.id,
            signal=signal.signal,
            confidence=signal.confidence,
            stake=stake,
        )

    except Exception as e:
        logger.error("strategy.trade_failed", error=str(e))


async def _get_basket_profit(session: UserSession, open_trades: List[Trade]) -> float:
    """Get total floating profit of all open basket trades from Deriv."""
    total = 0.0
    for trade in open_trades:
        if not trade.contract_id:
            continue
        try:
            details = await session.client.get_contract_details(int(trade.contract_id))
            total += float(details.get("profit", 0))
        except Exception:
            pass
    return total


def _get_basket_direction(open_trades: List[Trade]) -> Optional[str]:
    """Returns 'BUY', 'SELL', or None if basket is empty."""
    for trade in open_trades:
        if trade.contract_type == "CALL":
            return "BUY"
        if trade.contract_type == "PUT":
            return "SELL"
    return None


async def _close_all_basket(
    session: UserSession, open_trades: List[Trade], db: AsyncSession
) -> None:
    """Close all open basket trades on Deriv and update DB."""
    for trade in open_trades:
        if not trade.contract_id:
            continue
        try:
            sell_info = await session.client.sell_contract(int(trade.contract_id))
            sold_for = float(sell_info.get("sold_for", 0))
            profit = sold_for - trade.stake
            await trade_crud.close_trade(
                db,
                trade=trade,
                exit_price=float(sell_info.get("exit_spot", 0)),
                profit=profit,
                payout=sold_for,
            )
        except Exception as e:
            logger.warning("strategy.close_failed", trade_id=trade.id, error=str(e))
    await db.commit()


async def _send_notif(
    session: UserSession,
    db: AsyncSession,
    type_: str,
    title: str,
    body: str,
) -> None:
    """Save notification to DB and send push if FCM token available."""
    await notif_crud.create_notification(
        db, user_id=session.user_id, type_=type_, title=title, body=body
    )
    if session.fcm_token:
        asyncio.create_task(
            send_push_notification(token=session.fcm_token, title=title, body=body)
        )


# ─────────────────────────────────────────────────────────────────────────────
# Trade status monitor (every 5 seconds)
# ─────────────────────────────────────────────────────────────────────────────

async def _monitor_loop(session: UserSession) -> None:
    """Syncs open trade statuses with Deriv every 5 seconds."""
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
    """
    Check each open trade:
    1. MA cross exit — if enabled and MAs cross against position → sell early
    2. Trade status sync — if contract expired on Deriv → close in DB
    """
    from app.services.ai_engine import AIEngine
    from app.crud.strategy import get_strategy_settings

    open_trades = await trade_crud.get_open_trades(db, session.user_id)
    if not open_trades:
        return

    # Load strategy settings to check if MA cross exit is enabled
    strat = await get_strategy_settings(db, session.user_id)
    ma_exit_enabled = getattr(strat, "ma_cross_exit_enabled", False)

    for trade in open_trades:
        if not trade.contract_id:
            continue

        # ── Priority 1: MA Cross Exit ──────────────────────────────────────
        if ma_exit_enabled and session.client:
            try:
                engine = AIEngine(client=session.client, settings=strat)
                position_type = "BUY" if trade.contract_type == "CALL" else "SELL"
                should_exit, exit_reason = await engine.check_ma_cross_exit(
                    trade.symbol, position_type
                )
                if should_exit:
                    logger.info(
                        "monitor.ma_cross_exit",
                        trade_id=trade.id,
                        reason=exit_reason,
                    )
                    try:
                        sell_info = await session.client.sell_contract(
                            int(trade.contract_id)
                        )
                        sold_for = float(sell_info.get("sold_for", 0))
                        profit = sold_for - trade.stake
                        await trade_crud.close_trade(
                            db,
                            trade=trade,
                            exit_price=float(sell_info.get("exit_spot", 0)),
                            profit=profit,
                            payout=sold_for,
                        )
                        await _notify_trade_close_by_id(
                            session.user_id, session.fcm_token, trade, db
                        )
                        await _send_notif(
                            session, db, "ma_cross_exit",
                            "MA Cross Exit",
                            f"{trade.contract_type} on {trade.symbol} closed — {exit_reason}",
                        )
                        await db.commit()
                        continue  # trade closed — skip status check
                    except Exception as e:
                        logger.warning(
                            "monitor.ma_cross_sell_failed",
                            trade_id=trade.id,
                            error=str(e),
                        )
            except Exception as e:
                logger.warning(
                    "monitor.ma_cross_check_failed",
                    trade_id=trade.id,
                    error=str(e),
                )

        # ── Priority 2: Contract status sync (duration expired) ───────────
        try:
            details = await session.client.get_contract_details(
                int(trade.contract_id)
            )
            status = details.get("status")

            if status in ("won", "lost", "sold"):
                profit = float(details.get("profit", 0))
                payout = float(
                    details.get("sell_price") or details.get("bid_price") or 0
                )
                exit_price = float(
                    details.get("exit_tick") or details.get("sell_spot") or 0
                )
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
            logger.warning(
                "monitor.check_failed", trade_id=trade.id, error=str(e)
            )


# ─────────────────────────────────────────────────────────────────────────────
# Manual trade execution (from API)
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
    """Validate risk rules, place a contract on Deriv, and record it."""
    risk = await get_or_create_risk_settings(db, user.id)

    if risk.emergency_stop:
        raise RuntimeError("Emergency stop is active — trading halted")
    if not risk.trading_enabled:
        raise RuntimeError("Trading is disabled in risk settings")
    if stake > risk.max_stake:
        raise RuntimeError(f"Stake {stake} exceeds max allowed {risk.max_stake}")

    open_trades = await trade_crud.get_open_trades(db, user.id)
    if len(open_trades) >= risk.max_open_trades:
        raise RuntimeError(f"Max open trades ({risk.max_open_trades}) already reached")

    summary = await trade_crud.get_daily_summary(db, user.id)
    if summary["today_profit"] <= -abs(risk.max_daily_loss):
        raise RuntimeError("Daily loss limit reached — trading stopped for today")
    if ai_confidence is not None and ai_confidence < risk.min_ai_confidence:
        raise RuntimeError(
            f"AI confidence {ai_confidence:.2f} below minimum {risk.min_ai_confidence}"
        )

    session = _sessions.get(user.id)
    if session is None or session.client is None:
        raise RuntimeError("Trading session not active — call /trading/start first")

    contract = await session.client.buy_contract(
        symbol=symbol,
        contract_type=contract_type,
        stake=stake,
        duration=duration,
        duration_unit=duration_unit,
    )

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
        symbol=symbol,
        contract_type=contract_type,
        stake=stake,
    )
    return trade


async def close_trade_manually(
    trade: Trade, user: User, db: AsyncSession
) -> Trade:
    """Manually close an open trade before expiry."""
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
# Notification helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _notify_trade_close_by_id(
    user_id: int, fcm_token: Optional[str], trade: Trade, db: AsyncSession
) -> None:
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
    """Legacy wrapper."""
    await _notify_trade_close_by_id(user.id, user.fcm_token, trade, db)
