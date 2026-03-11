from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DBDep
from app.config import settings
from app.core.exceptions import AppException
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.schemas.auth import (
    RefreshRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: DBDep) -> UserResponse:
    """Register a new user account."""
    service = AuthService(db)
    try:
        user = await service.register_user(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except AppException as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: DBDep) -> TokenResponse:
    """Authenticate with email + password and receive JWT tokens."""
    service = AuthService(db)
    try:
        user = await service.login_user(email=payload.email, password=payload.password)
    except AppException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=str(user.id),
        algorithm=settings.JWT_ALGORITHM,
        secret_key=settings.SECRET_KEY,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        algorithm=settings.JWT_ALGORITHM,
        secret_key=settings.SECRET_KEY,
        expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: DBDep) -> TokenResponse:
    """Exchange a valid refresh token for a new token pair."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_payload = verify_token(
            payload.refresh_token,
            algorithm=settings.JWT_ALGORITHM,
            secret_key=settings.SECRET_KEY,
            expected_type="refresh",
        )
    except AppException:
        raise credentials_exc

    user_id = token_payload.get("sub")
    service = AuthService(db)
    try:
        user = await service.get_user_by_id(user_id)
    except AppException:
        raise credentials_exc

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    access_token = create_access_token(
        subject=str(user.id),
        algorithm=settings.JWT_ALGORITHM,
        secret_key=settings.SECRET_KEY,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    new_refresh_token = create_refresh_token(
        subject=str(user.id),
        algorithm=settings.JWT_ALGORITHM,
        secret_key=settings.SECRET_KEY,
        expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)
