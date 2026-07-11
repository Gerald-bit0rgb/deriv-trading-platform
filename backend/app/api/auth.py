"""
Authentication routes.

POST /api/v1/auth/register   — create a new user
POST /api/v1/auth/login      — get access + refresh tokens
POST /api/v1/auth/refresh    — get a new access token
GET  /api/v1/auth/me         — return the current user profile
PATCH /api/v1/auth/me        — update profile / FCM token
PUT  /api/v1/auth/token      — save the user's Deriv API token
DELETE /api/v1/auth/token    — remove the Deriv API token
"""
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.crud.user import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    update_deriv_token,
    update_fcm_token,
)
from app.crud.risk import get_or_create_risk_settings
from app.models.user import User
from app.schemas.user import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    UserUpdateToken,
)
from app.core.logging import get_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        has_deriv_token=bool(user.deriv_api_token),
        deriv_account_id=user.deriv_account_id,
        created_at=user.created_at,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    if await get_user_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")
    if await get_user_by_username(db, data.username):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")

    user = await create_user(db, data)
    # Create default risk settings for new user
    await get_or_create_risk_settings(db, user.id)

    access  = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))

    logger.info("auth.registered", user_id=user.id, email=user.email)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=_user_response(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate and return JWT tokens."""
    user = await get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    access  = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))

    logger.info("auth.login", user_id=user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=_user_response(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for a new access token."""
    credentials_error = HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
    )
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_error
        user_id = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise credentials_error

    from app.crud.user import get_user_by_id
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise credentials_error

    access  = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=_user_response(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Return the currently authenticated user's profile."""
    return _user_response(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile fields (full_name, FCM token)."""
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.fcm_token is not None:
        await update_fcm_token(db, current_user, data.fcm_token)
    return _user_response(current_user)


@router.put("/token", response_model=UserResponse)
async def save_deriv_token(
    data: UserUpdateToken,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Store the user's Deriv API token.

    The token is stored in the database (encrypted at rest via Postgres
    column-level encryption or full-disk encryption depending on your
    Render plan). It is NEVER written to logs.
    """
    await update_deriv_token(db, current_user, data.deriv_api_token)
    logger.info("auth.deriv_token_updated", user_id=current_user.id)
    return _user_response(current_user)


@router.delete("/token", response_model=UserResponse)
async def delete_deriv_token(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove the stored Deriv API token."""
    current_user.deriv_api_token = None
    await db.flush()
    logger.info("auth.deriv_token_removed", user_id=current_user.id)
    return _user_response(current_user)
