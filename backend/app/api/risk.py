"""
Risk management routes.

GET   /api/v1/risk        — get current risk settings
PUT   /api/v1/risk        — update risk settings
POST  /api/v1/risk/emergency-stop   — immediately halt all trading
POST  /api/v1/risk/emergency-reset  — clear emergency stop flag
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.crud.risk import get_or_create_risk_settings, update_risk_settings
from app.models.user import User
from app.schemas.risk import RiskSettingsResponse, RiskSettingsUpdate
from app.services import trading_engine
from app.core.logging import get_logger

router = APIRouter(prefix="/risk", tags=["Risk Management"])
logger = get_logger(__name__)


@router.get("", response_model=RiskSettingsResponse)
async def get_risk(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's risk management settings."""
    settings = await get_or_create_risk_settings(db, current_user.id)
    return settings


@router.put("", response_model=RiskSettingsResponse)
async def update_risk(
    data: RiskSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update risk management settings."""
    settings = await update_risk_settings(db, current_user.id, data)
    logger.info("risk.updated", user_id=current_user.id)
    return settings


@router.post("/emergency-stop")
async def emergency_stop(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    EMERGENCY STOP — immediately:
    1. Halts the trading bot
    2. Sets the emergency_stop flag in risk settings
    """
    # Stop the bot
    await trading_engine.stop_trading(current_user.id)

    # Set flag in DB
    settings = await get_or_create_risk_settings(db, current_user.id)
    settings.emergency_stop = True
    settings.trading_enabled = False
    await db.flush()

    logger.warning("risk.emergency_stop_activated", user_id=current_user.id)
    return {"message": "Emergency stop activated. All trading halted.", "status": "stopped"}


@router.post("/emergency-reset")
async def emergency_reset(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear the emergency stop flag and re-enable trading."""
    settings = await get_or_create_risk_settings(db, current_user.id)
    settings.emergency_stop = False
    settings.trading_enabled = True
    await db.flush()

    logger.info("risk.emergency_stop_cleared", user_id=current_user.id)
    return {"message": "Emergency stop cleared. Trading re-enabled.", "status": "ready"}
