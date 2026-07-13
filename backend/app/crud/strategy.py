"""
CRUD operations for StrategySettings.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.strategy_settings import StrategySettings
from app.schemas.strategy import StrategySettingsUpdate


async def get_strategy_settings(db: AsyncSession, user_id: int) -> StrategySettings:
    result = await db.execute(
        select(StrategySettings).where(StrategySettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = StrategySettings(user_id=user_id)
        db.add(settings)
        await db.flush()
    return settings


async def update_strategy_settings(
    db: AsyncSession, user_id: int, data: StrategySettingsUpdate
) -> StrategySettings:
    settings = await get_strategy_settings(db, user_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await db.flush()
    return settings
