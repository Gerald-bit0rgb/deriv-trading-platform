"""
Watchlist routes.

GET    /api/v1/watchlist           — get all watchlist symbols
POST   /api/v1/watchlist/{symbol}  — add symbol to watchlist
DELETE /api/v1/watchlist/{symbol}  — remove symbol from watchlist
DELETE /api/v1/watchlist           — clear entire watchlist
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.crud.watchlist import (
    add_to_watchlist,
    clear_watchlist,
    get_watchlist,
    remove_from_watchlist,
)
from app.models.user import User
from app.core.logging import get_logger

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])
logger = get_logger(__name__)

# Allowed symbols — same as the app's full symbol list
_ALLOWED_SYMBOLS = {
    "R_10", "R_25", "R_50", "R_75", "R_100",
    "1HZ10V", "1HZ25V", "1HZ50V", "1HZ75V", "1HZ100V",
    "JD10", "JD25", "JD50", "JD75", "JD100",
    "frxEURUSD", "frxGBPUSD", "frxUSDJPY", "frxAUDUSD", "frxUSDCAD", "frxXAUUSD",
}


@router.get("", response_model=List[str])
async def get_user_watchlist(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the list of symbols in the user's watchlist."""
    items = await get_watchlist(db, current_user.id)
    return [item.symbol for item in items]


@router.post("/{symbol}", status_code=status.HTTP_201_CREATED)
async def add_symbol(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a symbol to the watchlist."""
    symbol = symbol.upper()
    if symbol not in _ALLOWED_SYMBOLS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Symbol '{symbol}' is not supported",
        )
    item = await add_to_watchlist(db, current_user.id, symbol)
    logger.info("watchlist.added", user_id=current_user.id, symbol=symbol)
    return {"symbol": item.symbol, "message": f"{symbol} added to watchlist"}


@router.delete("/{symbol}")
async def remove_symbol(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a symbol from the watchlist."""
    symbol = symbol.upper()
    removed = await remove_from_watchlist(db, current_user.id, symbol)
    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{symbol} not in watchlist")
    logger.info("watchlist.removed", user_id=current_user.id, symbol=symbol)
    return {"message": f"{symbol} removed from watchlist"}


@router.delete("")
async def clear_user_watchlist(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear the entire watchlist."""
    await clear_watchlist(db, current_user.id)
    logger.info("watchlist.cleared", user_id=current_user.id)
    return {"message": "Watchlist cleared"}
