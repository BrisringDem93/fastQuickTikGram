from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AppException, NotFoundError
from app.core.security import verify_token
from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService

_bearer_scheme = HTTPBearer(auto_error=True)

DBDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DBDep,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
) -> User:
    """Validate Bearer JWT and return the authenticated User."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(
            credentials.credentials,
            algorithm=settings.JWT_ALGORITHM,
            secret_key=settings.SECRET_KEY,
            expected_type="access",
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except AppException:
        raise credentials_exception

    auth_service = AuthService(db)
    try:
        user = await auth_service.get_user_by_id(user_id)
    except NotFoundError:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
