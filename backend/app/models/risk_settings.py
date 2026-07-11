"""
RiskSettings model — one row per user, stores all risk management parameters.
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RiskSettings(Base):
    __tablename__ = "risk_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # ── Position sizing ───────────────────────────────────────────────────────
    default_stake: Mapped[float] = mapped_column(Float, default=1.0)        # per-trade stake in account currency
    max_stake: Mapped[float] = mapped_column(Float, default=10.0)

    # ── Daily limits ──────────────────────────────────────────────────────────
    max_daily_loss: Mapped[float] = mapped_column(Float, default=50.0)      # USD
    max_daily_trades: Mapped[int] = mapped_column(Integer, default=20)
    daily_profit_target: Mapped[float] = mapped_column(Float, default=100.0)

    # ── Concurrent positions ──────────────────────────────────────────────────
    max_open_trades: Mapped[int] = mapped_column(Integer, default=3)

    # ── Per-trade risk controls ───────────────────────────────────────────────
    take_profit_pct: Mapped[float] = mapped_column(Float, default=0.85)     # 85 % of payout
    stop_loss_pct: Mapped[float] = mapped_column(Float, default=1.0)        # lose full stake
    trailing_stop_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    trailing_stop_pct: Mapped[float] = mapped_column(Float, default=0.1)    # 10 %

    # ── Drawdown protection ───────────────────────────────────────────────────
    max_drawdown_pct: Mapped[float] = mapped_column(Float, default=20.0)    # % of starting balance

    # ── Emergency controls ───────────────────────────────────────────────────
    emergency_stop: Mapped[bool] = mapped_column(Boolean, default=False)    # kills all trading instantly
    trading_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── AI threshold ──────────────────────────────────────────────────────────
    min_ai_confidence: Mapped[float] = mapped_column(Float, default=0.65)   # only trade if AI >= this

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship
    user: Mapped["User"] = relationship(back_populates="risk_settings")

    def __repr__(self) -> str:
        return f"<RiskSettings user_id={self.user_id}>"
