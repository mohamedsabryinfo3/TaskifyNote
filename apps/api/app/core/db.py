from collections.abc import AsyncGenerator

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings


_engine = None
SessionLocal = None


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _engine, SessionLocal

    if SessionLocal is not None:
        return SessionLocal

    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    _engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
    )
    SessionLocal = async_sessionmaker(
        _engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    try:
        session_factory = _get_session_factory()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured on this deployment.",
        ) from exc

    async with session_factory() as session:
        yield session
