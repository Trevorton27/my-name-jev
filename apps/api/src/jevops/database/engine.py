from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from jevops.config import Settings


def create_engine(settings: Settings):
    return create_async_engine(
        settings.db.async_url,
        echo=settings.debug,
        pool_size=5,
        max_overflow=10,
    )


def create_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    engine = create_engine(settings)
    return async_sessionmaker(engine, expire_on_commit=False)
