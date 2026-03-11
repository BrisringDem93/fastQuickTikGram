from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedColumn


def _build_async_url(url: str) -> str:
    """Ensure the DB URL uses the asyncpg driver."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


# Import here to avoid circular imports at module load time.
# The engine is created lazily on first import via module-level code below.
from app.config import settings  # noqa: E402

_async_url = _build_async_url(settings.DATABASE_URL)

engine = create_async_engine(
    _async_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    # Subclasses can override __tablename__ manually; otherwise SQLAlchemy
    # requires it.  Leaving it abstract here.


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """FastAPI dependency that yields an AsyncSession and closes it afterwards."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
