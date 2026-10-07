from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: int = 0
    due_at: datetime | None = None

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: int | None = None
    status: str | None = None
    due_at: datetime | None = None

class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: str | None
    status: str
    priority: int
    due_at: datetime | None

class NoteCreate(BaseModel):
    title: str
    content: str = ""
    source_url: str | None = None

class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    source_url: str | None = None

class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    content: str
    source_url: str | None
