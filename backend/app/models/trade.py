"""
Trade model — records every trade executed through the platform.
Updated for lot-based trading (EA-style, not duration-based).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    contract_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # ── Lot-based trading (not duration, not stake) ────────────────────────────
    lot_size: Mapped[float] = mapped_column(Float, nullable=False, description="Lot size e.g. 0.01, 0.1, 1.0")
    
    # Entry/Exit prices and profit (in account currency)
    payout: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    entry_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Trade status and result ───────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    is_win: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # ── AI signal info ────────────────────────────────────────────────────────
    ai_signal: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Trade source (auto or manual) ─────────────────────────────────────────
    source: Mapped[str] = mapped_column(String(20), default="manual")

    # ── Timestamps ────────────────────────────────────────────────────────────
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="trades")

    def __repr__(self) -> str:
        return f"<Trade id={self.id} symbol={self.symbol!r} status={self.status!r} lots={self.lot_size}>"
