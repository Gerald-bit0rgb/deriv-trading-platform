"""
Strategy settings routes.

GET  /api/v1/strategy   — get current strategy settings
PUT  /api/v1/strategy   — update strategy settings
POST /api/v1/strategy/reset — reset to default settings
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.crud.strategy import get_strategy_settings, update_strategy_settings
from app.models.user import User
from app.schemas.strategy import StrategySettingsResponse, StrategySettingsUpdate
from app.core.logging import get_logger

router = APIRouter(prefix="/strategy", tags=["Strategy Settings"])
logger = get_logger(__name__)


@router.get("", response_model=StrategySettingsResponse)
async def get_strategy(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return current strategy settings. Returns defaults if not set."""
    settings = await get_strategy_settings(db, current_user.id)
    return settings


@router.put("", response_model=StrategySettingsResponse)
async def update_strategy(
    data: StrategySettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update strategy parameters."""
    settings = await update_strategy_settings(db, current_user.id, data)
    logger.info("strategy.updated", user_id=current_user.id)
    return settings


@router.post("/reset", response_model=StrategySettingsResponse)
async def reset_strategy(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset all strategy settings to EA defaults."""
    defaults = StrategySettingsUpdate()
    settings = await update_strategy_settings(db, current_user.id, defaults)
    logger.info("strategy.reset", user_id=current_user.id)
    return settings
