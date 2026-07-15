"""
Trading Engine — 1-Minute Microtrading Strategy (EA-style, Multiplier contracts)

Automated bot loop:
  Every new 1M bar:
    1. Run 1M microtrading analysis on all watchlist symbols
    2. If BUY/SELL signal with high confidence → open a MULTUP/MULTDOWN position
    3. Check open trades for crossback exit, trailing stop hits, or status sync
  Every 5 seconds:
    4. Check crossback exit signal (EMA crosses back through BB middle)
    5. Check trailing stop
    6. Sync any trades closed on Deriv's side (e.g. stop-out)

Settings (read from user's RiskSettings):
  default_lot_size    → lot size per entry
  max_lot_size        → per-trade lot cap
  daily_profit_target → daily stop (optional)

No fixed-duration exits — positions stay open until a crossback or trailing
stop closes them, same as an MT5 Expert Advisor.
"""
import asyncio
from enum import Enum
from typing import Dict, Optional

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

# Leverage used for Multiplier (MULTUP/MULTDOWN) contracts — EA-style positions
DEFAULT_MULTIPLIER = 100


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
        self._last_bar_time: Optional[int] = None   # last 1M bar epoch processed

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


# ── Session registry ────────────────────────────────────────────────────────
_sessions: Dict[int, UserSession] = {}


def get_session(user_id: int) -> Optional[UserSession]:
    return _sessions.get(user_id)


# ────────────────────────────────────────────────────────────────────────────
# Engine control
# ────────────────────────────────────────────────────────────────────────────

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

    # Background task 2: run 1M microtrading strategy on every new 1M bar
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


# ────────────────────────────────────────────────────────────────────────────
# 1M Microtrading Strategy Loop
# ────────────────────────────────────────────────────────────────────────────

async def _strategy_loop(session: UserSession) -> None:
    """
    Runs the 1M microtrading strategy on every new 1M bar.
    Checks every 30 seconds for a new bar.
    """
    logger.info("strategy.started", user_id=session.user_id)

    while session.status in (BotStatus.RUNNING, BotStatus.PAUSED):
        try:
            if session.status == BotStatus.RUNNING:
                async with session.db_factory() as db:
                    await _run_microtrading_loop(session, db)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("strategy.error", user_id=session.user_id, error=str(e))

        # Check every 30 seconds for a new 1M bar
        await asyncio.sleep(30)

    logger.info("strategy.stopped", user_id=session.user_id)


async def _run_microtrading_loop(session: UserSession, db: AsyncSession) -> None:
    """
    1M Microtrading strategy — multi-symbol watchlist edition.

    Every new bar:
      1. Load user's watchlist symbols (defaults: R_100, R_75, R_50)
      2. Use first symbol as the timing clock for new-bar detection
      3. Scan every watchlist symbol and trade qualifying signals
      4. Check open trades for exits (trailing stop or manual close)
    """
    from app.crud.strategy import get_strategy_settings as get_strat
    from app.crud.watchlist import get_watchlist_symbols

    if session.client is None:
        return

    # ── Settings ──────────────────────────────────────────────────────────────
    strat = await get_strat(db, session.user_id)
    risk = await get_or_create_risk_settings(db, session.user_id)

    if risk.emergency_stop or not risk.trading_enabled:
        return

    # ── Load watchlist symbols ────────────────────────────────────────────────
    symbols = await get_watchlist_symbols(db, session.user_id)
    # symbols is never empty — get_watchlist_symbols returns DEFAULT_SYMBOLS

    # ── New-bar check using the first symbol as clock ──────────────────────
    clock_symbol = symbols[0]
    try:
        candles = await session.client.get_candles(
            clock_symbol, granularity=60, count=5
        )
        if not candles:
            logger.warning("strategy.no_candles_returned",
                           user_id=session.user_id, symbol=clock_symbol)
            return
        current_bar_epoch = int(candles[-2].get("epoch", 0))
        if current_bar_epoch == session._last_bar_time:
            logger.info("strategy.same_bar_skipping", user_id=session.user_id)
            return
        session._last_bar_time = current_bar_epoch
        logger.info("strategy.new_bar_processing",
                    user_id=session.user_id,
                    epoch=current_bar_epoch,
                    symbols=symbols)
    except Exception as e:
        logger.error("strategy.bar_check_failed",
                     user_id=session.user_id,
                     symbol=clock_symbol,
                     error=str(e))
        return

    # ── Get all open trades once ───────────────────────────────────────────
    all_open = await trade_crud.get_open_trades(db, session.user_id)

    # ── Daily loss guard ──────────────────────────────────────────────────
    summary = await trade_crud.get_daily_summary(db, session.user_id)
    if summary["today_profit"] <= -abs(risk.max_daily_loss):
        logger.info("strategy.daily_loss_limit_reached", user_id=session.user_id)
        return

    # ── Symbols already holding an open trade ──────────────────────────────
    open_symbols = {t.symbol for t in all_open}

    # ── Scan every watchlist symbol and trade qualifying signals ─────────
    for symbol in symbols:
        await _analyse_and_trade_symbol(
            session=session,
            db=db,
            symbol=symbol,
            strat=strat,
            risk=risk,
            open_symbols=open_symbols,
        )
        # Update open_symbols after each trade attempt
        refreshed = await trade_crud.get_open_trades(db, session.user_id)
        open_symbols = {t.symbol for t in refreshed}


async def _analyse_and_trade_symbol(
    session: UserSession,
    db: AsyncSession,
    symbol: str,
    strat,
    risk,
    open_symbols: set,
) -> None:
    """
    Analyse one symbol and place a trade if the signal qualifies.

    Rules:
      - Skip if symbol already has an open trade
      - Skip if signal is WAIT
      - Skip if confidence is below user's min_ai_confidence threshold
    """
    from app.services.ai_engine import AIEngine

    # One trade per symbol at a time
    if symbol in open_symbols:
        logger.info("strategy.symbol_already_open",
                    user_id=session.user_id, symbol=symbol)
        return

    # Analyse
    try:
        engine = AIEngine(client=session.client, settings=strat)
        signal = await engine.analyse(symbol, granularity=60)
        logger.info(
            "strategy.analysis_result",
            user_id=session.user_id,
            symbol=symbol,
            signal=signal.signal,
            confidence=signal.confidence,
            ema3=signal.ema3_value,
            bb_mid=signal.bb_middle,
            macd_hist=signal.macd_histogram,
            rsi=signal.rsi_value,
        )
    except Exception as e:
        logger.error("strategy.analysis_failed",
                     user_id=session.user_id, symbol=symbol, error=str(e))
        return

    # Gate: WAIT
    if signal.signal == "WAIT":
        return

    # Gate: confidence threshold (set by user in risk settings)
    if signal.confidence < risk.min_ai_confidence:
        logger.info(
            "strategy.confidence_too_low",
            user_id=session.user_id,
            symbol=symbol,
            confidence=signal.confidence,
            min_required=risk.min_ai_confidence,
        )
        return

    # ── Place trade (EA-style: Multiplier contract, no duration) ────────────
    contract_type = "MULTUP" if signal.signal == "BUY" else "MULTDOWN"
    lot_size = min(risk.default_lot_size, risk.max_lot_size)

    try:
        contract = await session.client.buy_contract(
            symbol=symbol,
            contract_type=contract_type,
            amount=lot_size,
            multiplier=DEFAULT_MULTIPLIER,
        )

        trade = await trade_crud.create_trade(
            db,
            user_id=session.user_id,
            contract_id=str(contract.get("contract_id")),
            symbol=symbol,
            contract_type=contract_type,
            lot_size=lot_size,
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
            f"1M {signal.signal} — {symbol}",
            f"{contract_type} | Lots: {lot_size} | EMA3: {signal.ema3_value:.5f} | "
            f"RSI: {signal.rsi_value:.1f}% | Conf: {int(signal.confidence * 100)}%",
        )

        logger.info(
            "strategy.trade_placed",
            user_id=session.user_id,
            trade_id=trade.id,
            symbol=symbol,
            signal=signal.signal,
            confidence=signal.confidence,
            lot_size=lot_size,
        )

    except Exception as e:
        logger.error("strategy.trade_failed",
                     user_id=session.user_id, symbol=symbol, error=str(e))


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


# ────────────────────────────────────────────────────────────────────────────
# Trade status monitor (every 5 seconds)
# ────────────────────────────────────────────────────────────────────────────

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
    Check each open trade, in priority order:
    1. Crossback exit — the strategy's real exit rule (EMA crosses back through BB middle)
    2. Trailing stop — if enabled, protects profit once a trade is winning
    3. Status sync — catches contracts closed on Deriv's side (e.g. stop-out)
    """
    from app.crud.strategy import get_strategy_settings
    from app.services.ai_engine import AIEngine

    open_trades = await trade_crud.get_open_trades(db, session.user_id)
    if not open_trades:
        return

    strat = await get_strategy_settings(db, session.user_id)

    for trade in open_trades:
        if not trade.contract_id:
            continue

        # ── Priority 1: Crossback exit (the strategy's real exit signal) ──
        if strat.exit_on_crossback_enabled and session.client:
            try:
                trade_direction = "BUY" if trade.contract_type == "MULTUP" else "SELL"
                engine = AIEngine(client=session.client, settings=strat)
                should_exit = await engine.check_exit_signal(
                    trade.symbol, trade_direction, granularity=60
                )
                if should_exit:
                    try:
                        sell_info = await session.client.sell_contract(int(trade.contract_id))
                        sold_for = float(sell_info.get("sold_for", 0))
                        profit = float(sell_info.get("profit", sold_for))
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
                            session, db, "crossback_exit",
                            "Crossback Exit",
                            f"{trade.contract_type} on {trade.symbol} closed | Profit: ${profit:.2f}",
                        )
                        await db.commit()
                        continue
                    except Exception as e:
                        logger.warning(
                            "monitor.crossback_sell_failed",
                            trade_id=trade.id,
                            error=str(e),
                        )
            except Exception as e:
                logger.warning(
                    "monitor.crossback_check_failed",
                    trade_id=trade.id,
                    error=str(e),
                )

        # ── Priority 2: Trailing Stop ──────────────────────────────────────
        if strat.trailing_stop_enabled and session.client:
            try:
                details = await session.client.get_contract_details(int(trade.contract_id))
                current_profit = float(details.get("profit", 0))
                trailing_stop_dist = strat.trailing_stop_distance

                # If trade is winning and hits trailing stop
                if current_profit > 0 and current_profit <= trailing_stop_dist:
                    logger.info(
                        "monitor.trailing_stop_hit",
                        trade_id=trade.id,
                        profit=current_profit,
                    )
                    try:
                        sell_info = await session.client.sell_contract(
                            int(trade.contract_id)
                        )
                        sold_for = float(sell_info.get("sold_for", 0))
                        profit = float(sell_info.get("profit", sold_for))
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
                            session, db, "trailing_stop",
                            "Trailing Stop Hit",
                            f"{trade.contract_type} on {trade.symbol} closed | Profit: ${profit:.2f}",
                        )
                        await db.commit()
                        continue
                    except Exception as e:
                        logger.warning(
                            "monitor.trailing_stop_sell_failed",
                            trade_id=trade.id,
                            error=str(e),
                        )
            except Exception as e:
                logger.warning(
                    "monitor.trailing_stop_check_failed",
                    trade_id=trade.id,
                    error=str(e),
                )

        # ── Priority 3: Status sync — catches contracts closed on Deriv's
        # side outside our control (e.g. stop-out from insufficient margin) ──
        try:
            details = await session.client.get_contract_details(
                int(trade.contract_id)
            )
            status = details.get("status")

            if status in ("sold", "stopped_out"):
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


# ────────────────────────────────────────────────────────────────────────────
# Manual trade execution (from API)
# ────────────────────────────────────────────────────────────────────────────

async def execute_trade(
    user: User,
    symbol: str,
    contract_type: str,
    lot_size: float,
    db: AsyncSession,
    ai_signal: Optional[str] = None,
    ai_confidence: Optional[float] = None,
    ai_reason: Optional[str] = None,
    source: str = "manual",
) -> Trade:
    """
    Validate risk rules, open an EA-style Multiplier position on Deriv, and record it.

    contract_type: "MULTUP" (buy/long) or "MULTDOWN" (sell/short)
    """
    risk = await get_or_create_risk_settings(db, user.id)

    if risk.emergency_stop:
        raise RuntimeError("Emergency stop is active — trading halted")
    if not risk.trading_enabled:
        raise RuntimeError("Trading is disabled in risk settings")
    if lot_size > risk.max_lot_size:
        raise RuntimeError(f"Lot size {lot_size} exceeds max allowed {risk.max_lot_size}")

    summary = await trade_crud.get_daily_summary(db, user.id)
    if summary["today_profit"] <= -abs(risk.max_daily_loss):
        raise RuntimeError("Daily loss limit reached — trading stopped for today")
    if summary["today_trades"] >= risk.max_daily_trades:
        raise RuntimeError(f"Daily trade limit ({risk.max_daily_trades}) already reached")
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
        amount=lot_size,
        multiplier=DEFAULT_MULTIPLIER,
    )

    trade = await trade_crud.create_trade(
        db,
        user_id=user.id,
        contract_id=str(contract.get("contract_id")),
        symbol=symbol,
        contract_type=contract_type,
        lot_size=lot_size,
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
        body=f"{contract_type} on {symbol} | Lots: {lot_size}",
    )
    if user.fcm_token:
        asyncio.create_task(
            send_push_notification(
                token=user.fcm_token,
                title="Trade Opened",
                body=f"{contract_type} on {symbol} | Lots: {lot_size}",
            )
        )

    logger.info(
        "trade.executed",
        user_id=user.id,
        trade_id=trade.id,
        symbol=symbol,
        contract_type=contract_type,
        lot_size=lot_size,
    )
    return trade


async def close_trade_manually(
    trade: Trade, user: User, db: AsyncSession
) -> Trade:
    """Manually close an open EA-style position."""
    session = _sessions.get(user.id)
    if session is None or session.client is None:
        raise RuntimeError("Trading session not active")

    sell_info = await session.client.sell_contract(int(trade.contract_id))
    sold_for = float(sell_info.get("sold_for", 0))
    profit = float(sell_info.get("profit", sold_for))

    updated = await trade_crud.close_trade(
        db,
        trade=trade,
        exit_price=float(sell_info.get("exit_spot", 0)),
        profit=profit,
        payout=sold_for,
    )
    await _notify_trade_close_by_id(user.id, user.fcm_token, updated, db)
    return updated


# ────────────────────────────────────────────────────────────────────────────
# Notification helpers
# ────────────────────────────────────────────────────────────────────────────

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
