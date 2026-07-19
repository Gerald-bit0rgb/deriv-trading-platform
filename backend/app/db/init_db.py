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

    # ── Safe migrations — add new columns if they don't exist ────────────────
    # These use IF NOT EXISTS so they are safe to run on every startup.
    #
    # IMPORTANT: each migration runs in its OWN transaction (a fresh
    # engine.begin() per statement), not one shared transaction for the
    # whole list. Postgres aborts an entire transaction on the first error
    # within it and refuses every further command until it's rolled back —
    # so a single shared transaction meant one failing migration would
    # silently no-op every migration listed after it, even though each
    # failure was individually logged as if it were independent. Isolating
    # each migration in its own transaction means a failure only affects
    # that one statement.
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
        # ── 1M entry-confirmation columns (EMA3/BB18/MACD/RSI) ────────────────
        # These were never migrated when the strategy moved off the original
        # MA Bias Basket schema — this is the actual root cause of
        # "column strategy_settings.ema_fast_period does not exist".
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS entry_timeframe INTEGER DEFAULT 60
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS ema_fast_period INTEGER DEFAULT 3
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS ema_applied_price VARCHAR(10) DEFAULT 'CLOSE'
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS bb_period INTEGER DEFAULT 18
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS bb_std_dev FLOAT DEFAULT 2.0
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS bb_method VARCHAR(10) DEFAULT 'SMA'
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS macd_fast INTEGER DEFAULT 12
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS macd_slow INTEGER DEFAULT 26
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS macd_signal INTEGER DEFAULT 9
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS rsi_period INTEGER DEFAULT 14
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS rsi_overbought FLOAT DEFAULT 70.0
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS rsi_oversold FLOAT DEFAULT 30.0
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS exit_on_crossback_enabled BOOLEAN DEFAULT TRUE
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now()
        """,
        # ── ATR-based Stop Loss / Take Profit (optional feature) ──────────────
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS use_atr_sl_tp BOOLEAN DEFAULT FALSE
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS atr_period INTEGER DEFAULT 14
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS atr_sl_multiplier FLOAT DEFAULT 1.5
        """,
        """
        ALTER TABLE strategy_settings
        ADD COLUMN IF NOT EXISTS atr_tp_multiplier FLOAT DEFAULT 2.0
        """,
        # ── Relax NOT NULL on orphaned legacy columns ──────────────────────────
        # The live trades table still carries columns from the very original
        # binary-options schema (stake, duration, duration_unit, take_profit,
        # stop_loss) that the current code doesn't know about and never sets.
        # If any of these are still NOT NULL with no default, every insert
        # from the current ORM fails outright. DROP NOT NULL (not DROP
        # COLUMN) is deliberately conservative: keeps historical data intact,
        # safe no-op if a column is already nullable or doesn't exist.
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'trades' AND column_name = 'stake'
            ) THEN
                ALTER TABLE trades ALTER COLUMN stake DROP NOT NULL;
            END IF;
        END $$
        """,
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'trades' AND column_name = 'duration'
            ) THEN
                ALTER TABLE trades ALTER COLUMN duration DROP NOT NULL;
            END IF;
        END $$
        """,
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'trades' AND column_name = 'duration_unit'
            ) THEN
                ALTER TABLE trades ALTER COLUMN duration_unit DROP NOT NULL;
            END IF;
        END $$
        """,
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'trades' AND column_name = 'take_profit'
            ) THEN
                ALTER TABLE trades ALTER COLUMN take_profit DROP NOT NULL;
            END IF;
        END $$
        """,
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'trades' AND column_name = 'stop_loss'
            ) THEN
                ALTER TABLE trades ALTER COLUMN stop_loss DROP NOT NULL;
            END IF;
        END $$
        """,
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'risk_settings' AND column_name = 'default_stake'
            ) THEN
                ALTER TABLE risk_settings ALTER COLUMN default_stake DROP NOT NULL;
            END IF;
        END $$
        """,
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'risk_settings' AND column_name = 'max_stake'
            ) THEN
                ALTER TABLE risk_settings ALTER COLUMN max_stake DROP NOT NULL;
            END IF;
        END $$
        """,
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'risk_settings' AND column_name = 'max_open_trades'
            ) THEN
                ALTER TABLE risk_settings ALTER COLUMN max_open_trades DROP NOT NULL;
            END IF;
        END $$
        """,
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'strategy_settings' AND column_name = 'bias_fast_period'
            ) THEN
                ALTER TABLE strategy_settings ALTER COLUMN bias_fast_period DROP NOT NULL;
            END IF;
        END $$
        """,
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'strategy_settings' AND column_name = 'bias_slow_period'
            ) THEN
                ALTER TABLE strategy_settings ALTER COLUMN bias_slow_period DROP NOT NULL;
            END IF;
        END $$
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS stop_loss_price FLOAT
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS take_profit_price FLOAT
        """,
        # ── Trades: full defensive coverage (every non-key column) ───────────
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS lot_size FLOAT NOT NULL DEFAULT 0.01
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS contract_id VARCHAR(100)
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS symbol VARCHAR(50) NOT NULL DEFAULT 'R_100'
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS contract_type VARCHAR(50) NOT NULL DEFAULT 'MULTUP'
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS payout FLOAT
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS profit FLOAT
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS entry_price FLOAT
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS exit_price FLOAT
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'open'
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS is_win BOOLEAN
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS ai_signal VARCHAR(10)
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS ai_confidence FLOAT
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS ai_reason TEXT
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'manual'
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS opened_at TIMESTAMPTZ DEFAULT now()
        """,
        """
        ALTER TABLE trades
        ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ
        """,
        # ── Risk settings: full defensive coverage ────────────────────────────
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS default_lot_size FLOAT DEFAULT 1.0
        """,
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS max_lot_size FLOAT DEFAULT 100.0
        """,
        # ── Repair existing stake values below Deriv's $1.00 minimum ──────────
        # "lot_size" fields are a direct USD stake, not an MT5-style lot
        # multiplier — earlier defaults of 0.01/1.0 were below what Deriv's
        # Multiplier API actually accepts, causing every auto-trade to fail
        # with "Please enter a stake amount that's at least 1.00." This
        # bumps any already-saved values up to a valid stake so existing
        # users aren't stuck with a broken configuration after this update.
        """
        UPDATE risk_settings SET default_lot_size = 1.0 WHERE default_lot_size < 1.0
        """,
        """
        UPDATE risk_settings SET max_lot_size = 100.0 WHERE max_lot_size < 1.0
        """,
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS max_daily_loss FLOAT DEFAULT 50.0
        """,
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS max_daily_trades INTEGER DEFAULT 100
        """,
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS daily_profit_target FLOAT DEFAULT 200.0
        """,
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS max_drawdown_pct FLOAT DEFAULT 20.0
        """,
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS trailing_stop_enabled BOOLEAN DEFAULT TRUE
        """,
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS trailing_stop_distance FLOAT DEFAULT 2.0
        """,
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS emergency_stop BOOLEAN DEFAULT FALSE
        """,
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS trading_enabled BOOLEAN DEFAULT TRUE
        """,
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS min_ai_confidence FLOAT DEFAULT 0.65
        """,
        """
        ALTER TABLE risk_settings
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now()
        """,
        # ── Users: defensive coverage for optional columns ────────────────────
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS full_name VARCHAR(200)
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS deriv_api_token TEXT
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS deriv_account_id VARCHAR(100)
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS fcm_token TEXT
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now()
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now()
        """,
        # ── Bot sessions / notifications / watchlist: defensive coverage ──────
        """
        ALTER TABLE bot_sessions
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE
        """,
        """
        ALTER TABLE bot_sessions
        ADD COLUMN IF NOT EXISTS symbol VARCHAR(20) DEFAULT 'R_100'
        """,
        """
        ALTER TABLE bot_sessions
        ADD COLUMN IF NOT EXISTS account_type VARCHAR(10) DEFAULT 'demo'
        """,
        """
        ALTER TABLE bot_sessions
        ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ
        """,
        """
        ALTER TABLE bot_sessions
        ADD COLUMN IF NOT EXISTS stopped_at TIMESTAMPTZ
        """,
        """
        ALTER TABLE notifications
        ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE
        """,
        """
        ALTER TABLE notifications
        ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ DEFAULT now()
        """,
        """
        ALTER TABLE watchlist
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
        """,
        """
        ALTER TABLE watchlist
        ADD COLUMN IF NOT EXISTS added_at TIMESTAMPTZ DEFAULT now()
        """,
    ]
    applied, skipped = 0, 0
    for sql in migrations:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(sql.strip()))
            applied += 1
        except Exception as e:
            skipped += 1
            logger.warning("migration.skipped", error=str(e))

    logger.info("database.tables_created", migrations_applied=applied, migrations_skipped=skipped)


if __name__ == "__main__":
    asyncio.run(init_db())
