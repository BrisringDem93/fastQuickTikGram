from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.user import User


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def register_user(
        self, *, email: str, password: str, full_name: str
    ) -> User:
        """Create a new user. Raises AppException if email already taken."""
        existing = await self._db.scalar(select(User).where(User.email == email.lower()))
        if existing is not None:
            raise AppException(f"An account with email '{email}' already exists")

        user = User(
            email=email.lower(),
            hashed_password=hash_password(password),
            full_name=full_name,
            is_active=True,
            is_verified=False,
        )
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def login_user(self, *, email: str, password: str) -> User:
        """Verify credentials and return the User. Raises AppException on failure."""
        user = await self._db.scalar(select(User).where(User.email == email.lower()))
        if user is None or not verify_password(password, user.hashed_password):
            raise AppException("Invalid email or password")
        if not user.is_active:
            raise AppException("Account is deactivated")
        return user

    async def get_user_by_id(self, user_id: str | uuid.UUID) -> User:
        """Fetch a User by primary key. Raises NotFoundError if absent."""
        user = await self._db.get(User, uuid.UUID(str(user_id)))
        if user is None:
            raise NotFoundError("User", user_id)
        return user

    async def refresh_token(self, user_id: str | uuid.UUID) -> User:
        """Return the user associated with a refresh-token subject claim."""
        return await self.get_user_by_id(user_id)
