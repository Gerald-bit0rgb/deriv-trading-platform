"""
User model — stores account credentials and the Deriv API token.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.trade import Trade
    from app.models.risk_settings import RiskSettings
    from app.models.notification import Notification
    from app.models.strategy_settings import StrategySettings
    from app.models.bot_session import BotSession
    from app.models.watchlist import WatchlistItem


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    deriv_api_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deriv_account_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    fcm_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    trades: Mapped[List["Trade"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    risk_settings: Mapped[Optional["RiskSettings"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    strategy_settings: Mapped[Optional["StrategySettings"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    bot_session: Mapped[Optional["BotSession"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    watchlist: Mapped[List["WatchlistItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
