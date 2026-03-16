from __future__ import annotations

import asyncio
import logging

from app.database import Base, engine

# Ensure model metadata is registered before create_all()
import app.models  # noqa: F401

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Create all ORM tables if they do not exist yet."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Initializing database schema...")
    asyncio.run(init_db())
    logger.info("Database schema initialization complete.")
