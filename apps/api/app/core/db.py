from collections.abc import AsyncGenerator
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from .config import settings


_engine = None
SessionLocal = None


def _normalize_postgres_dsn(raw_url: str) -> str:
    url = raw_url.strip()

    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]

    if url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + url[len("postgresql+asyncpg://"):]

    if not url.startswith("postgresql://"):
        raise ValueError("DATABASE_URL must be a PostgreSQL connection URL")

    return url


def _get_sqlalchemy_url(raw_url: str) -> str:
    return "postgresql+psycopg://" + _normalize_postgres_dsn(raw_url)[len("postgresql://"):]


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _engine, SessionLocal

    if SessionLocal is not None:
        return SessionLocal

    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    _engine = create_async_engine(
        _get_sqlalchemy_url(settings.database_url),
        poolclass=NullPool,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
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
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database configuration error: {exc.__class__.__name__}",
        ) from exc

    try:
        async with session_factory() as session:
            yield session
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database operation failed: {exc.__class__.__name__}",
        ) from exc
