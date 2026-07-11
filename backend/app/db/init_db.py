"""
Database initialisation helper.

Called at startup to create all tables that don't exist yet.
In production you should use Alembic migrations instead of create_all.
"""
import asyncio

from app.core.logging import get_logger
from app.db.session import Base, engine

# Import all models so SQLAlchemy knows about them
from app.models import user, trade, risk_settings, notification  # noqa: F401

logger = get_logger(__name__)


async def init_db() -> None:
    """Create all database tables if they don't already exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database.tables_created")


if __name__ == "__main__":
    asyncio.run(init_db())
