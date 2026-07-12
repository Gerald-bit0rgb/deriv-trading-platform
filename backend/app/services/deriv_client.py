"""
Deriv WebSocket API client.

Features:
  - Async WebSocket connection using the official Deriv WS API
  - Automatic reconnection with exponential back-off
  - Request/response correlation via req_id
  - Subscription management (tick streams, portfolio, etc.)
  - Full logging of every API call and response
  - API token is NEVER logged
"""
import asyncio
import json
from typing import Callable, Dict, Optional

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Maximum seconds between reconnect attempts
_MAX_BACKOFF = 60


class DerivClient:
    """
    Persistent WebSocket connection to the Deriv API.

    Usage:
        client = DerivClient(api_token="TOKEN")
        await client.connect()
        balance = await client.get_balance()
        await client.disconnect()
    """

    def __init__(self, api_token: str, app_id: int = None):
        self._api_token = api_token          # never logged
        self._app_id = app_id or settings.DERIV_APP_ID
        self._ws_url = f"{settings.DERIV_WS_URL}?app_id={self._app_id}"

        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._req_id: int = 1
        self._pending: Dict[int, asyncio.Future] = {}
        self._subscriptions: Dict[str, Callable] = {}  # subscription_id -> callback
        self._connected = False
        self._should_run = False
        self._listener_task: Optional[asyncio.Task] = None
        self._reconnect_attempts = 0

    # ─────────────────────────────────────────────────────────────────────────
    # Connection management
    # ─────────────────────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Establish WebSocket connection and authorise with the API token."""
        self._should_run = True
        await self._do_connect()

    async def _do_connect(self) -> None:
        backoff = min(2 ** self._reconnect_attempts, _MAX_BACKOFF)
        if self._reconnect_attempts > 0:
            logger.info("deriv.reconnecting", attempt=self._reconnect_attempts, backoff=backoff)
            await asyncio.sleep(backoff)

        try:
            self._ws = await websockets.connect(
                self._ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )
            self._connected = True
            self._reconnect_attempts = 0
            logger.info("deriv.connected", url=self._ws_url)

            # Start background listener
            self._listener_task = asyncio.create_task(self._listen())

            # Authorise immediately
            await self._authorize()

        except (WebSocketException, OSError, asyncio.TimeoutError) as exc:
            self._connected = False
            self._reconnect_attempts += 1
            logger.warning("deriv.connect_failed", error=str(exc), attempt=self._reconnect_attempts)
            if self._should_run:
                await self._do_connect()

    async def disconnect(self) -> None:
        """Gracefully close the connection."""
        self._should_run = False
        self._connected = False
        if self._listener_task:
            self._listener_task.cancel()
        if self._ws:
            await self._ws.close()
        logger.info("deriv.disconnected")

    async def _listen(self) -> None:
        """Background task: read incoming messages and resolve futures."""
        try:
            async for raw in self._ws:
                try:
                    msg: dict = json.loads(raw)
                    await self._dispatch(msg)
                except json.JSONDecodeError as e:
                    logger.warning("deriv.bad_json", error=str(e))
        except (ConnectionClosed, WebSocketException) as exc:
            self._connected = False
            logger.warning("deriv.connection_lost", error=str(exc))
            # Cancel all pending requests with an error
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(exc)
            self._pending.clear()
            if self._should_run:
                self._reconnect_attempts += 1
                asyncio.create_task(self._do_connect())

    async def _dispatch(self, msg: dict) -> None:
        """Route an incoming message to a pending future or a subscription callback."""
        req_id = msg.get("req_id")
        error = msg.get("error")

        # Log everything except sensitive fields
        safe = {k: v for k, v in msg.items() if k not in ("authorize", "token")}
        logger.debug("deriv.message_received", msg=safe)

        # Resolve a waiting coroutine
        if req_id and req_id in self._pending:
            fut = self._pending.pop(req_id)
            if not fut.done():
                if error:
                    fut.set_exception(RuntimeError(error.get("message", "Deriv API error")))
                else:
                    fut.set_result(msg)
            return

        # Subscription stream (tick, portfolio, etc.)
        sub_id = msg.get("subscription", {}).get("id")
        if sub_id and sub_id in self._subscriptions:
            try:
                await self._subscriptions[sub_id](msg)
            except Exception as e:
                logger.error("deriv.subscription_callback_error", sub_id=sub_id, error=str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # Low-level send
    # ─────────────────────────────────────────────────────────────────────────

    async def _send(self, payload: dict, timeout: float = 15.0) -> dict:
        """
        Send a request and await its response.

        Raises RuntimeError if the API returns an error field.
        """
        if not self._connected or not self._ws:
            raise RuntimeError("Deriv WebSocket not connected")

        req_id = self._req_id
        self._req_id += 1
        payload["req_id"] = req_id

        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[req_id] = fut

        # Log request — omit token value
        safe_payload = {k: v for k, v in payload.items() if k != "authorize"}
        logger.info("deriv.request", req_id=req_id, payload=safe_payload)

        await self._ws.send(json.dumps(payload))

        try:
            response = await asyncio.wait_for(fut, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise RuntimeError(f"Deriv API request timed out (req_id={req_id})")

    # ─────────────────────────────────────────────────────────────────────────
    # Auth
    # ─────────────────────────────────────────────────────────────────────────

    async def _authorize(self) -> dict:
        """Authorise the connection with the stored API token."""
        response = await self._send({"authorize": self._api_token})
        account = response.get("authorize", {})
        logger.info("deriv.authorized", loginid=account.get("loginid"), currency=account.get("currency"))
        return response

    # ─────────────────────────────────────────────────────────────────────────
    # Account
    # ─────────────────────────────────────────────────────────────────────────

    async def get_balance(self) -> dict:
        """Return current account balance."""
        response = await self._send({"balance": 1})
        return response.get("balance", {})

    async def get_account_info(self) -> dict:
        """Return account statement / info."""
        response = await self._send({"get_account_status": 1})
        return response.get("get_account_status", {})

    async def get_profit_table(self, limit: int = 25, offset: int = 0) -> dict:
        """Retrieve closed contract history."""
        response = await self._send({
            "profit_table": 1,
            "limit": limit,
            "offset": offset,
            "sort": "DESC",
        })
        return response.get("profit_table", {})

    # ─────────────────────────────────────────────────────────────────────────
    # Market data
    # ─────────────────────────────────────────────────────────────────────────

    async def get_ticks(self, symbol: str) -> dict:
        """Get the latest tick for a symbol (one-shot)."""
        response = await self._send({"ticks": symbol})
        return response.get("tick", {})

    async def subscribe_ticks(self, symbol: str, callback: Callable) -> str:
        """
        Subscribe to live tick stream.

        :param callback: async function(msg: dict) called on each tick.
        :returns:        subscription ID (use to unsubscribe).
        """
        response = await self._send({"ticks": symbol, "subscribe": 1})
        sub_id = response.get("subscription", {}).get("id")
        if sub_id:
            self._subscriptions[sub_id] = callback
            logger.info("deriv.subscribed_ticks", symbol=symbol, sub_id=sub_id)
        return sub_id

    async def unsubscribe(self, sub_id: str) -> None:
        """Cancel a live subscription."""
        await self._send({"forget": sub_id})
        self._subscriptions.pop(sub_id, None)
        logger.info("deriv.unsubscribed", sub_id=sub_id)

    async def unsubscribe_all(self) -> None:
        """Cancel all active subscriptions."""
        for sub_id in list(self._subscriptions.keys()):
            try:
                await self.unsubscribe(sub_id)
            except Exception:
                pass

    async def get_candles(self, symbol: str, granularity: int = 60, count: int = 200) -> list:
        """
        Retrieve OHLC candle data.

        :param granularity: candle size in seconds (60=1m, 3600=1h, 86400=1d)
        :param count:       number of candles
        """
        response = await self._send({
            "ticks_history": symbol,
            "style": "candles",
            "granularity": granularity,
            "count": count,
            "end": "latest",
        })
        return response.get("candles", [])

    # ─────────────────────────────────────────────────────────────────────────
    # Trading
    # ─────────────────────────────────────────────────────────────────────────

    async def buy_contract(
        self,
        symbol: str,
        contract_type: str,
        stake: float,
        duration: int,
        duration_unit: str = "t",
    ) -> dict:
        """
        Place a new contract.

        :param contract_type: "CALL" (buy/rise) or "PUT" (sell/fall)
        :param duration_unit: "t"=ticks, "s"=seconds, "m"=minutes, "h"=hours, "d"=days
        :returns: full buy response including contract_id
        """
        # First get a price proposal
        proposal = await self._send({
            "proposal": 1,
            "amount": stake,
            "basis": "stake",
            "contract_type": contract_type,
            "currency": "USD",
            "duration": duration,
            "duration_unit": duration_unit,
            "symbol": symbol,
        })
        proposal_id = proposal.get("proposal", {}).get("id")
        if not proposal_id:
            raise RuntimeError(f"Failed to get proposal: {proposal}")

        # Buy the proposal
        buy_response = await self._send({"buy": proposal_id, "price": stake})
        contract = buy_response.get("buy", {})
        logger.info(
            "deriv.trade_placed",
            contract_id=contract.get("contract_id"),
            symbol=symbol,
            contract_type=contract_type,
            stake=stake,
        )
        return contract

    async def sell_contract(self, contract_id: int, price: float = 0) -> dict:
        """
        Sell / close an open contract early.

        :param price: minimum acceptable sell price (0 = any price)
        """
        response = await self._send({"sell": contract_id, "price": price})
        sell_info = response.get("sell", {})
        logger.info("deriv.trade_sold", contract_id=contract_id, sold_for=sell_info.get("sold_for"))
        return sell_info

    async def get_open_contracts(self) -> list:
        """Return all currently open contracts for this account."""
        response = await self._send({"portfolio": 1})
        return response.get("portfolio", {}).get("contracts", [])

    async def get_contract_details(self, contract_id: int) -> dict:
        """Fetch full details of one contract."""
        response = await self._send({
            "proposal_open_contract": 1,
            "contract_id": contract_id,
        })
        return response.get("proposal_open_contract", {})
