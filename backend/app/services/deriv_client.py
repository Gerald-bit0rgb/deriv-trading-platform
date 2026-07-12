"""
Deriv API client — supports the new API with pat_ tokens.

Flow:
  1. Use PAT token as Bearer in REST calls to api.derivws.com
  2. Get account list via REST
  3. Get OTP (one-time password) for the account via REST
  4. Connect to WebSocket using the OTP URL (no authorize step needed)
  5. Trade using the same WebSocket message format as before
"""
import asyncio
import json
from typing import Callable, Dict, List, Optional

import httpx
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# New Deriv API base URL
_REST_BASE = "https://api.derivws.com"
_MAX_BACKOFF = 60


class DerivClient:
    """
    Deriv API client supporting pat_ tokens via the new Options API.
    """

    def __init__(self, api_token: str, app_id: int = None):
        self._api_token = api_token
        self._app_id = app_id or settings.DERIV_APP_ID
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._ws_url: Optional[str] = None
        self._account_id: Optional[str] = None
        self._account_type: Optional[str] = None  # "demo" or "real"
        self._req_id: int = 1
        self._pending: Dict[int, asyncio.Future] = {}
        self._subscriptions: Dict[str, Callable] = {}
        self._connected = False
        self._should_run = False
        self._listener_task: Optional[asyncio.Task] = None
        self._reconnect_attempts = 0

    # ─────────────────────────────────────────────────────────────────────────
    # REST helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _rest_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_token}",
            "Deriv-App-ID": str(self._app_id).strip(),
            "Content-Type": "application/json",
        }

    async def _rest_get(self, path: str) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{_REST_BASE}{path}", headers=self._rest_headers())
            if r.status_code != 200:
                raise RuntimeError(
                    f"Deriv REST GET {path} failed: {r.status_code} {r.text}"
                )
            return r.json()

    async def _rest_post(self, path: str, body: dict = None) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{_REST_BASE}{path}",
                headers=self._rest_headers(),
                json=body or {},
            )
            if r.status_code not in (200, 201):
                raise RuntimeError(
                    f"Deriv REST POST {path} failed: {r.status_code} {r.text}"
                )
            return r.json()

    # ─────────────────────────────────────────────────────────────────────────
    # Connection management
    # ─────────────────────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Connect to Deriv using the new PAT token flow."""
        self._should_run = True
        await self._do_connect()

    async def _do_connect(self) -> None:
        backoff = min(2 ** self._reconnect_attempts, _MAX_BACKOFF)
        if self._reconnect_attempts > 0:
            logger.info("deriv.reconnecting", attempt=self._reconnect_attempts, backoff=backoff)
            await asyncio.sleep(backoff)

        try:
            # Step 1 — Get accounts list
            accounts_resp = await self._rest_get("/trading/v1/options/accounts")
            accounts: List[dict] = accounts_resp.get("data", [])

            if not accounts:
                # No account exists — create a demo one
                logger.info("deriv.no_account_found_creating_demo")
                create_resp = await self._rest_post(
                    "/trading/v1/options/accounts",
                    {"currency": "USD", "group": "row", "account_type": "demo"},
                )
                accounts = create_resp.get("data", [])

            if not accounts:
                raise RuntimeError("Could not get or create a Deriv trading account")

            # Prefer demo account for safety; fall back to first available
            account = next(
                (a for a in accounts if a.get("account_type") == "demo"),
                accounts[0],
            )
            self._account_id = account["account_id"]
            self._account_type = account.get("account_type", "demo")
            logger.info(
                "deriv.account_selected",
                account_id=self._account_id,
                account_type=self._account_type,
            )

            # Step 2 — Get OTP WebSocket URL
            otp_resp = await self._rest_post(
                f"/trading/v1/options/accounts/{self._account_id}/otp"
            )
            ws_url = otp_resp.get("data", {}).get("url")
            if not ws_url:
                raise RuntimeError(f"No WebSocket URL in OTP response: {otp_resp}")

            self._ws_url = ws_url
            logger.info("deriv.otp_obtained", account_id=self._account_id)

            # Step 3 — Connect WebSocket (already authenticated via OTP)
            self._ws = await websockets.connect(
                self._ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )
            self._connected = True
            self._reconnect_attempts = 0
            logger.info("deriv.connected", account_id=self._account_id)

            # Start listener
            self._listener_task = asyncio.create_task(self._listen())

        except (WebSocketException, OSError, asyncio.TimeoutError) as exc:
            self._connected = False
            self._reconnect_attempts += 1
            logger.warning("deriv.connect_failed_network", error=str(exc))
            if self._should_run:
                await self._do_connect()
        except RuntimeError as exc:
            self._connected = False
            logger.error("deriv.connect_failed", error=str(exc))
            raise

    async def disconnect(self) -> None:
        self._should_run = False
        self._connected = False
        if self._listener_task:
            self._listener_task.cancel()
        if self._ws:
            await self._ws.close()
        logger.info("deriv.disconnected")

    async def _listen(self) -> None:
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
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(exc)
            self._pending.clear()
            if self._should_run:
                self._reconnect_attempts += 1
                asyncio.create_task(self._do_connect())

    async def _dispatch(self, msg: dict) -> None:
        req_id = msg.get("req_id")
        error = msg.get("error")

        if req_id and req_id in self._pending:
            fut = self._pending.pop(req_id)
            if not fut.done():
                if error:
                    fut.set_exception(RuntimeError(error.get("message", "Deriv API error")))
                else:
                    fut.set_result(msg)
            return

        sub_id = msg.get("subscription", {}).get("id")
        if sub_id and sub_id in self._subscriptions:
            try:
                await self._subscriptions[sub_id](msg)
            except Exception as e:
                logger.error("deriv.subscription_callback_error", error=str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # Low-level WebSocket send
    # ─────────────────────────────────────────────────────────────────────────

    async def _send(self, payload: dict, timeout: float = 15.0) -> dict:
        if not self._connected or not self._ws:
            raise RuntimeError("Deriv WebSocket not connected")

        req_id = self._req_id
        self._req_id += 1
        payload["req_id"] = req_id

        loop = asyncio.get_event_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[req_id] = fut

        await self._ws.send(json.dumps(payload))

        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise RuntimeError(f"Deriv request timed out (req_id={req_id})")

    # ─────────────────────────────────────────────────────────────────────────
    # Account
    # ─────────────────────────────────────────────────────────────────────────

    async def get_balance(self) -> dict:
        response = await self._send({"balance": 1})
        return response.get("balance", {})

    async def get_account_info(self) -> dict:
        return await self._rest_get("/trading/v1/options/accounts")

    async def get_profit_table(self, limit: int = 25, offset: int = 0) -> dict:
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
        response = await self._send({"ticks": symbol})
        return response.get("tick", {})

    async def subscribe_ticks(self, symbol: str, callback: Callable) -> str:
        response = await self._send({"ticks": symbol, "subscribe": 1})
        sub_id = response.get("subscription", {}).get("id")
        if sub_id:
            self._subscriptions[sub_id] = callback
        return sub_id

    async def unsubscribe(self, sub_id: str) -> None:
        await self._send({"forget": sub_id})
        self._subscriptions.pop(sub_id, None)

    async def unsubscribe_all(self) -> None:
        for sub_id in list(self._subscriptions.keys()):
            try:
                await self.unsubscribe(sub_id)
            except Exception:
                pass

    async def get_candles(self, symbol: str, granularity: int = 60, count: int = 200) -> list:
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
        # Get proposal
        proposal = await self._send({
            "proposal": 1,
            "amount": stake,
            "basis": "stake",
            "contract_type": contract_type,
            "currency": "USD",
            "duration": duration,
            "duration_unit": duration_unit,
            "underlying_symbol": symbol,
        })
        proposal_id = proposal.get("proposal", {}).get("id")
        ask_price = proposal.get("proposal", {}).get("ask_price", stake)

        if not proposal_id:
            raise RuntimeError(f"Failed to get proposal: {proposal}")

        # Buy
        buy_response = await self._send({"buy": proposal_id, "price": ask_price})
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
        response = await self._send({"sell": contract_id, "price": price})
        return response.get("sell", {})

    async def get_open_contracts(self) -> list:
        response = await self._send({"portfolio": 1})
        return response.get("portfolio", {}).get("contracts", [])

    async def get_contract_details(self, contract_id: int) -> dict:
        response = await self._send({
            "proposal_open_contract": 1,
            "contract_id": contract_id,
        })
        return response.get("proposal_open_contract", {})
