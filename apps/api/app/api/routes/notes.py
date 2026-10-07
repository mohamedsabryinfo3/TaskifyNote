from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.db import get_db
from ...models import Note
from ...schemas import NoteCreate, NoteOut, NoteUpdate

router = APIRouter(prefix="/notes", tags=["Notes"])

@router.get("", response_model=list[NoteOut])
async def list_notes(db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Note).where(Note.deleted_at.is_(None)).order_by(Note.updated_at.desc()))).scalars().all()

@router.post("", response_model=NoteOut, status_code=201)
async def create_note(payload: NoteCreate, db: AsyncSession = Depends(get_db)):
    note = Note(**payload.model_dump())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note

@router.patch("/{note_id}", response_model=NoteOut)
async def update_note(note_id: UUID, payload: NoteUpdate, db: AsyncSession = Depends(get_db)):
    note = await db.get(Note, note_id)
    if not note or note.deleted_at:
        raise HTTPException(404, "Note not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(note, key, value)
    await db.commit()
    await db.refresh(note)
    return note

@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: UUID, db: AsyncSession = Depends(get_db)):
    note = await db.get(Note, note_id)
    if not note or note.deleted_at:
        raise HTTPException(404, "Note not found")
    from datetime import datetime, timezone
    note.deleted_at = datetime.now(timezone.utc)
    await db.commit()
