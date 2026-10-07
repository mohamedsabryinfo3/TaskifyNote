from urllib.parse import urlsplit

from fastapi import APIRouter

from ...core.config import settings
from ...core.db import _normalize_postgres_dsn

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    return {
        "name": "TaskifyNote",
        "version": "0.7.8",
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
        import psycopg
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.pool import NullPool

        dsn = _normalize_postgres_dsn(settings.database_url)
        parts = urlsplit(dsn)

        # Direct async Psycopg 3 connection for a minimal connectivity test.
        async with await psycopg.AsyncConnection.connect(
            dsn,
            connect_timeout=5,
        ) as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT 1")
                await cursor.fetchone()

        engine = create_async_engine(
            "postgresql+psycopg://" + dsn[len("postgresql://"):],
            poolclass=NullPool,
            connect_args={"connect_timeout": 5},
        )
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        """
                        SELECT
                            to_regclass('public.tasks') IS NOT NULL AS tasks_exists,
                            to_regclass('public.notes') IS NOT NULL AS notes_exists
                        """
                    )
                )
                row = result.mappings().one()
        finally:
            await engine.dispose()

        return {
            "status": "ok",
            "database_connected": True,
            "host": parts.hostname,
            "database": parts.path.lstrip("/") or None,
            "tasks_table": row["tasks_exists"],
            "notes_table": row["notes_exists"],
        }
    except Exception as exc:
        return {
            "status": "error",
            "database_connected": False,
            "error_type": exc.__class__.__name__,
            "driver": "psycopg3",
        }
