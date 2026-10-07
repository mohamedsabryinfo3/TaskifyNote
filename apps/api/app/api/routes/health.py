from urllib.parse import urlsplit

from fastapi import APIRouter

from ...core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    return {
        "name": "TaskifyNote",
        "version": "0.7.7",
        "status": "ok",
        "database_configured": bool(settings.database_url),
    }


@router.get("/health/db")
async def database_health():
    if not settings.database_url:
        return {
            "status": "error",
            "database_connected": False,
            "error_type": "DATABASE_URL_NOT_CONFIGURED",
        }

    try:
        import asyncpg

        from ...core.db import _normalize_postgres_dsn

        dsn = _normalize_postgres_dsn(settings.database_url)
        parts = urlsplit(dsn)

        connection = await asyncpg.connect(dsn=dsn, timeout=3)
        try:
            await connection.execute("SET statement_timeout = '3000ms'")
            await connection.fetchval("SELECT 1")
        finally:
            await connection.close()

        return {
            "status": "ok",
            "database_connected": True,
            "host": parts.hostname,
            "database": parts.path.lstrip("/") or None,
        }
    except Exception as exc:
        return {
            "status": "error",
            "database_connected": False,
            "error_type": exc.__class__.__name__,
            "driver": "asyncpg",
        }
