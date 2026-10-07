from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.db import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    return {
        "name": "TaskifyNote",
        "version": "0.7.5",
        "status": "ok",
    }


@router.get("/health/db")
async def database_health(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            text(
                """
                SELECT
                    current_database() AS database_name,
                    to_regclass('public.tasks') IS NOT NULL AS tasks_exists,
                    to_regclass('public.notes') IS NOT NULL AS notes_exists
                """
            )
        )
        row = result.mappings().one()
        return {
            "status": "ok",
            "database_connected": True,
            "tasks_table": row["tasks_exists"],
            "notes_table": row["notes_exists"],
        }
    except Exception as exc:
        return {
            "status": "error",
            "database_connected": False,
            "error_type": exc.__class__.__name__,
        }
