"""
Trade model — records every trade executed through the platform.
"""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Deriv contract details
    contract_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)          # e.g. "R_100"
    contract_type: Mapped[str] = mapped_column(String(50), nullable=False)   # e.g. "CALL", "PUT"
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)     # in seconds / ticks
    duration_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "s", "t", "m", "h", "d"

    # Financial
    stake: Mapped[float] = mapped_column(Float, nullable=False)
    payout: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Entry / exit prices
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Status: open | closed | cancelled | error
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    is_win: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # AI signal that triggered this trade
    ai_signal: Mapped[str | None] = mapped_column(String(10), nullable=True)   # BUY | SELL | WAIT
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0 – 1.0
    ai_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source: manual | auto | ai
    source: Mapped[str] = mapped_column(String(20), default="manual")

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="trades")

    def __repr__(self) -> str:
        return f"<Trade id={self.id} symbol={self.symbol!r} status={self.status!r}>"
