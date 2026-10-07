from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.db import get_db
from ...models import Note, Task

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("")
async def search(q: str = Query(min_length=1), db: AsyncSession = Depends(get_db)):
    p = f"%{q}%"
    tasks = (await db.execute(select(Task).where(Task.deleted_at.is_(None), or_(Task.title.ilike(p), Task.description.ilike(p))).limit(20))).scalars().all()
    notes = (await db.execute(select(Note).where(Note.deleted_at.is_(None), or_(Note.title.ilike(p), Note.content.ilike(p))).limit(20))).scalars().all()
    return {
      "query": q,
      "results": [
        *[{"type":"task","id":str(x.id),"title":x.title,"snippet":(x.description or "")[:240]} for x in tasks],
        *[{"type":"note","id":str(x.id),"title":x.title,"snippet":x.content[:240]} for x in notes]
      ]
    }
