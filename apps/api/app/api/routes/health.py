from urllib.parse import urlsplit

import asyncpg
from fastapi import APIRouter

from ...core.config import settings
from ...core.db import _normalize_postgres_dsn

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    return {
        "name": "TaskifyNote",
        "version": "0.7.5",
        "status": "ok",
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
        dsn = _normalize_postgres_dsn(settings.database_url)
        parts = urlsplit(dsn)

        connection = await asyncpg.connect(
            dsn=dsn,
            timeout=10,
        )
        try:
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
