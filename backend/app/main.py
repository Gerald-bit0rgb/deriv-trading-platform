"""
FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload

Or via Docker / Render — see Dockerfile / render.yaml.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import (
    auth_router,
    trading_router,
    risk_router,
    ai_router,
    dashboard_router,
    notifications_router,
)
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.init_db import init_db

# ─────────────────────────────────────────────────────────────────────────────
# Startup / shutdown lifecycle
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Called once at startup and once at shutdown."""
    setup_logging()
    logger = get_logger("startup")
    logger.info("app.starting", env=settings.APP_ENV)

    # Create database tables
    await init_db()
    logger.info("app.database_ready")

    yield  # application runs here

    # Graceful shutdown — stop all active trading sessions
    from app.services.trading_engine import _sessions, stop_trading
    logger.info("app.shutting_down", active_sessions=len(_sessions))
    for user_id in list(_sessions.keys()):
        try:
            await stop_trading(user_id)
        except Exception as e:
            logger.error("app.shutdown_session_error", user_id=user_id, error=str(e))
    logger.info("app.stopped")


# ─────────────────────────────────────────────────────────────────────────────
# Rate limiter
# ─────────────────────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# ─────────────────────────────────────────────────────────────────────────────
# Application factory
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered automated trading platform for Deriv",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,      # disable Swagger in prod
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── Rate limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Trusted host (prevents Host-header injection in production) ───────────────
if not settings.DEBUG:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


# ─────────────────────────────────────────────────────────────────────────────
# Global exception handlers
# ─────────────────────────────────────────────────────────────────────────────

logger = get_logger("app")


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    error_detail = str(exc)
    tb = traceback.format_exc()
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=error_detail,
        traceback=tb,
    )
    # Return full error detail so we can debug
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": error_detail,
            "type": type(exc).__name__,
            "traceback": tb,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

PREFIX = settings.API_V1_PREFIX

app.include_router(auth_router,           prefix=PREFIX)
app.include_router(trading_router,        prefix=PREFIX)
app.include_router(risk_router,           prefix=PREFIX)
app.include_router(ai_router,             prefix=PREFIX)
app.include_router(dashboard_router,      prefix=PREFIX)
app.include_router(notifications_router,  prefix=PREFIX)


# ─────────────────────────────────────────────────────────────────────────────
# Health check (no auth required — used by Render and Docker)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    """Returns 200 OK when the service is up."""
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs" if settings.DEBUG else "disabled in production",
        "health": "/health",
    }
