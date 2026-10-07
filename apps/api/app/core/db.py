from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings


_engine = None
SessionLocal = None


def _normalize_database_url(raw_url: str) -> str:
    url = raw_url.strip()

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    parts = urlsplit(url)
    query = []

    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "sslmode":
            query.append(("ssl", value))
        elif key == "channel_binding":
            # channel_binding is not an asyncpg connection argument.
            continue
        else:
            query.append((key, value))

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            parts.fragment,
        )
    )


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _engine, SessionLocal

    if SessionLocal is not None:
        return SessionLocal

    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    database_url = _normalize_database_url(settings.database_url)

    _engine = create_async_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        connect_args={"statement_cache_size": 0},
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
