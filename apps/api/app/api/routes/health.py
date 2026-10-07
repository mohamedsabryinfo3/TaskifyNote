from urllib.parse import urlsplit

from fastapi import APIRouter

from ...core.config import settings
from ...core.db import _normalize_postgres_dsn, _get_session_factory
from ...models import Note

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

        dsn = _normalize_postgres_dsn(settings.database_url)
        parts = urlsplit(dsn)

        async with await psycopg.AsyncConnection.connect(
            dsn,
            connect_timeout=5,
        ) as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT 1")
                await cursor.fetchone()

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
            "driver": "psycopg3",
        }


@router.get("/health/notes-write")
async def notes_write_health():
    try:
        factory = _get_session_factory()
        async with factory() as session:
            async with session.begin():
                probe = Note(
                    title="__taskifynote_probe__",
                    content="probe",
                )
                session.add(probe)
                await session.flush()
                probe_id = str(probe.id)
                await session.rollback()

        return {
            "status": "ok",
            "notes_write": True,
            "rolled_back": True,
            "probe_id_created": bool(probe_id),
        }
    except Exception as exc:
        return {
            "status": "error",
            "notes_write": False,
            "error_type": exc.__class__.__name__,
        }



@router.get("/health/ai")
async def ai_health():
    return {
        "status": "ok",
        "ai_configured": bool(settings.gemini_api_key),
        "model": settings.ai_model,
    }
