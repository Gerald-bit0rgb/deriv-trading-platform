# API package — exposes all routers
from app.api.auth import router as auth_router
from app.api.trading import router as trading_router
from app.api.risk import router as risk_router
from app.api.ai import router as ai_router
from app.api.dashboard import router as dashboard_router
from app.api.notifications import router as notifications_router

__all__ = [
    "auth_router",
    "trading_router",
    "risk_router",
    "ai_router",
    "dashboard_router",
    "notifications_router",
]
