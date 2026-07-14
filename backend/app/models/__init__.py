# Re-export all models so `from app.models import *` works everywhere
from app.models.user import User
from app.models.trade import Trade
from app.models.risk_settings import RiskSettings
from app.models.notification import Notification
from app.models.strategy_settings import StrategySettings
from app.models.bot_session import BotSession
from app.models.watchlist import WatchlistItem

__all__ = ["User", "Trade", "RiskSettings", "Notification", "StrategySettings", "BotSession", "WatchlistItem"]
