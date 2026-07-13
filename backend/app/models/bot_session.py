"""
BotSession model — persists bot state so it survives server restarts.
When the server restarts, it reads this table and restarts all active bots.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class BotSession(Base):
    __tablename__ = "bot_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False
    )

    # Bot is marked active when user taps Start Bot
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    # Trading symbol and account type saved so we can restart correctly
    symbol: Mapped[str] = mapped_column(String(20), default="R_100")
    account_type: Mapped[str] = mapped_column(String(10), default="demo")

    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    stopped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="bot_session")

    def __repr__(self) -> str:
        return f"<BotSession user_id={self.user_id} active={self.is_active}>"
