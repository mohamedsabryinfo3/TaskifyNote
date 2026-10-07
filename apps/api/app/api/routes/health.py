from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import asyncpg
from fastapi import APIRouter

from ...core.config import settings
from ...core.db import _normalize_postgres_dsn

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    return {
        "name": "TaskifyNote",
        "version": "0.7.6",
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
        dsn = _normalize_postgres_dsn(settings.database_url)
        parts = urlsplit(dsn)

        # Keep connection attempts well below typical serverless execution limits.
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


@router.get("/health/env")
async def environment_health():
    return {
        "status": "ok",
        "database_url_configured": bool(settings.database_url),
        "cors_configured": bool(settings.cors_origins),
        "app_env": settings.app_env,
        "database_scheme": (
            urlsplit(settings.database_url).scheme if settings.database_url else None
        ),
    }
