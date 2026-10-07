import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from ...core.config import settings
from ...core.db import _get_session_factory
from ...models import Note, Task

router = APIRouter(prefix="/ai", tags=["AI"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


def _build_context(tasks: list[Task], notes: list[Note]) -> str:
    task_lines = [
        f"- [{task.status}] {task.title} (priority={task.priority})"
        for task in tasks[:25]
    ]
    note_lines = [
        f"- {note.title}: {note.content[:700]}"
        for note in notes[:12]
    ]

    return (
        "Current TaskifyNote workspace context:\n"
        "Tasks:\n"
        + ("\n".join(task_lines) if task_lines else "- No tasks yet.")
        + "\nNotes:\n"
        + ("\n".join(note_lines) if note_lines else "- No notes yet.")
    )


def _generate(prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model=settings.ai_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are TaskifyNote, a private personal productivity assistant. "
                "Be practical and concise. Use the workspace context when relevant. "
                "Never invent tasks or notes. When recommending priorities, explain "
                "briefly why. Do not claim to have changed data unless an API action "
                "actually occurred."
            ),
            temperature=0.3,
            max_output_tokens=700,
        ),
    )
    return (response.text or "").strip()


@router.post("/chat")
async def chat(payload: ChatRequest):
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured.",
        )

    try:
        factory = _get_session_factory()
        async with factory() as db:
            tasks = (
                await db.execute(
                    select(Task)
                    .where(Task.deleted_at.is_(None))
                    .order_by(Task.due_at.nullslast(), Task.created_at.desc())
                    .limit(25)
                )
            ).scalars().all()

            notes = (
                await db.execute(
                    select(Note)
                    .where(Note.deleted_at.is_(None))
                    .order_by(Note.updated_at.desc())
                    .limit(12)
                )
            ).scalars().all()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Workspace context unavailable: {exc.__class__.__name__}",
        ) from exc

    prompt = f"{_build_context(tasks, notes)}\n\nUser request:\n{payload.message}"

    try:
        answer = await asyncio.to_thread(_generate, prompt)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider request failed: {exc.__class__.__name__}",
        ) from exc

    if not answer:
        raise HTTPException(status_code=502, detail="AI returned an empty response.")

    return {
        "message": answer,
        "input": payload.message,
        "model": settings.ai_model,
        "actions": [],
    }
