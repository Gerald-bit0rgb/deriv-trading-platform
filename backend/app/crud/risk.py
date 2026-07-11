"""
CRUD operations for RiskSettings.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk_settings import RiskSettings
from app.schemas.risk import RiskSettingsUpdate


async def get_risk_settings(db: AsyncSession, user_id: int) -> Optional[RiskSettings]:
    result = await db.execute(
        select(RiskSettings).where(RiskSettings.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_risk_settings(db: AsyncSession, user_id: int) -> RiskSettings:
    """Return existing settings or create default ones."""
    settings = await get_risk_settings(db, user_id)
    if settings is None:
        settings = RiskSettings(user_id=user_id)
        db.add(settings)
        await db.flush()
    return settings


async def update_risk_settings(
    db: AsyncSession, user_id: int, data: RiskSettingsUpdate
) -> RiskSettings:
    settings = await get_or_create_risk_settings(db, user_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    await db.flush()
    return settings
