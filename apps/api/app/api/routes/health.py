from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import asyncpg

from ...core.db import _normalize_database_url, get_db
from ...core.config import settings

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

    database_url = _normalize_database_url(settings.database_url)

    try:
        connection = await asyncpg.connect(
            database_url,
            timeout=10,
        )
        try:
            await connection.fetchval("SELECT 1")
        finally:
            await connection.close()

        return {
            "status": "ok",
            "database_connected": True,
        }
    except Exception as exc:
        return {
            "status": "error",
            "database_connected": False,
            "error_type": exc.__class__.__name__,
            "driver": "asyncpg",
        }
