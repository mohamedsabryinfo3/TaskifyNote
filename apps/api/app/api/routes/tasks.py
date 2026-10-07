from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.db import get_db
from ...models import Task
from ...schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("", response_model=list[TaskOut])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Task).where(Task.deleted_at.is_(None)).order_by(Task.due_at.nullslast(), Task.created_at.desc()))).scalars().all()
    return rows

@router.post("", response_model=TaskOut, status_code=201)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = Task(**payload.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: UUID, payload: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task or task.deleted_at:
        raise HTTPException(404, "Task not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task

@router.post("/{task_id}/complete", response_model=TaskOut)
async def complete_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task or task.deleted_at:
        raise HTTPException(404, "Task not found")
    from datetime import datetime, timezone
    task.status = "done"
    task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task or task.deleted_at:
        raise HTTPException(404, "Task not found")
    from datetime import datetime, timezone
    task.deleted_at = datetime.now(timezone.utc)
    await db.commit()
