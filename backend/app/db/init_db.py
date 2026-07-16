"""
Database initialisation helper.

Called at startup to create all tables that don't exist yet.
In production you should use Alembic migrations instead of create_all.
"""
import asyncio

from sqlalchemy import text

from app.core.logging import get_logger
from app.db.session import Base, engine

# Import all models so SQLAlchemy knows about them
from app.models import user, trade, risk_settings, notification, strategy_settings, bot_session, watchlist  # noqa: F401

logger = get_logger(__name__)


async def init_db() -> None:
    """Create all database tables if they don't already exist.
    Also runs safe ALTER TABLE migrations for new columns.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # ── Safe migrations — add new columns if they don't exist ────────────
        # These use IF NOT EXISTS so they are safe to run on every startup
        migrations = [
            """
            ALTER TABLE strategy_settings
            ADD COLUMN IF NOT EXISTS require_candle_confirmation BOOLEAN DEFAULT FALSE
            """,
            """
            UPDATE strategy_settings
            SET require_candle_confirmation = FALSE
            WHERE require_candle_confirmation = TRUE
            """,
            """
            ALTER TABLE strategy_settings
            ADD COLUMN IF NOT EXISTS ma_cross_exit_enabled BOOLEAN DEFAULT FALSE
            """,
            # ── Trend direction filter (4H EMA5/13 gate) ─────────────────────────
            """
            ALTER TABLE strategy_settings
            ADD COLUMN IF NOT EXISTS require_trend_alignment BOOLEAN DEFAULT TRUE
            """,
            """
            ALTER TABLE strategy_settings
            ADD COLUMN IF NOT EXISTS trend_timeframe INTEGER DEFAULT 14400
            """,
            """
            ALTER TABLE strategy_settings
            ADD COLUMN IF NOT EXISTS trend_fast_period INTEGER DEFAULT 5
            """,
            """
            ALTER TABLE strategy_settings
            ADD COLUMN IF NOT EXISTS trend_slow_period INTEGER DEFAULT 13
            """,
            """
            ALTER TABLE strategy_settings
            ADD COLUMN IF NOT EXISTS trend_ma_method VARCHAR(10) DEFAULT 'EMA'
            """,
            """
            ALTER TABLE strategy_settings
            ADD COLUMN IF NOT EXISTS trend_applied_price VARCHAR(10) DEFAULT 'CLOSE'
            """,
            # ── Trades: lot-based trading (was stake/duration) ───────────────────
            # DEFAULT is required here — existing rows need a value backfilled
            # since lot_size is NOT NULL on the model.
            """
            ALTER TABLE trades
            ADD COLUMN IF NOT EXISTS lot_size FLOAT NOT NULL DEFAULT 0.01
            """,
            # ── Risk settings: lot-based trading (was stake-based) ───────────────
            """
            ALTER TABLE risk_settings
            ADD COLUMN IF NOT EXISTS default_lot_size FLOAT DEFAULT 0.01
            """,
            """
            ALTER TABLE risk_settings
            ADD COLUMN IF NOT EXISTS max_lot_size FLOAT DEFAULT 1.0
            """,
        ]
        for sql in migrations:
            try:
                await conn.execute(text(sql.strip()))
            except Exception as e:
                logger.warning("migration.skipped", error=str(e))

    logger.info("database.tables_created")


if __name__ == "__main__":
    asyncio.run(init_db())
