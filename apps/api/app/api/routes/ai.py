import asyncio
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from ...core.config import settings
from ...core.db import _get_session_factory
from ...models import Note, Task

router = APIRouter(prefix="/ai", tags=["AI"])


AgentId = Literal["general", "planner", "task-manager", "note-analyst", "focus-coach"]

AGENTS: dict[str, dict[str, str]] = {
    "general": {
        "name": "General Assistant",
        "description": "Your all-purpose TaskifyNote assistant.",
        "instruction": (
            "Help the user with practical productivity questions, using the workspace "
            "context when relevant. Keep answers concise and actionable."
        ),
    },
    "planner": {
        "name": "Daily Planner",
        "description": "Builds a realistic plan and prioritizes what matters most.",
        "instruction": (
            "Act as a daily planning specialist. Identify the most important work, "
            "sequence tasks sensibly, flag blockers, and propose a realistic next-step "
            "plan. Do not invent deadlines or commitments."
        ),
    },
    "task-manager": {
        "name": "Task Manager",
        "description": "Turns ideas into clear, executable tasks.",
        "instruction": (
            "Act as an execution-focused task manager. Break vague goals into small, "
            "clear next actions, suggest priorities, and identify what can be deferred. "
            "Do not claim to create or modify tasks unless an API action actually occurs."
        ),
    },
    "note-analyst": {
        "name": "Note Analyst",
        "description": "Finds insights, summaries, and action items in saved notes.",
        "instruction": (
            "Act as a notes and knowledge analyst. Summarize relevant notes, connect "
            "related ideas, extract action items, and distinguish facts from suggestions. "
            "Never fabricate content that is not present in the workspace."
        ),
    },
    "focus-coach": {
        "name": "Focus Coach",
        "description": "Helps you choose one clear next move and avoid overload.",
        "instruction": (
            "Act as a focused productivity coach. Reduce cognitive overload, recommend "
            "one clear next action, and use short practical guidance. Prefer momentum over "
            "large plans when the user is stuck."
        ),
    },
}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    agent_id: AgentId = "general"


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


def _generate(prompt: str, agent_id: str) -> str:
    from google import genai
    from google.genai import types

    agent = AGENTS[agent_id]
    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model=settings.ai_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are TaskifyNote, a private personal productivity assistant. "
                f"You are currently operating as the '{agent['name']}'. "
                f"{agent['instruction']} "
                "Use the workspace context when relevant. Never invent tasks or notes. "
                "When recommending priorities, explain briefly why. Do not claim to have "
                "changed data unless an API action actually occurred."
            ),
            temperature=0.3,
            max_output_tokens=700,
        ),
    )
    return (response.text or "").strip()


@router.get("/agents")
async def list_agents():
    return {
        "default_agent": "general",
        "agents": [
            {
                "id": agent_id,
                "name": agent["name"],
                "description": agent["description"],
            }
            for agent_id, agent in AGENTS.items()
        ],
        "model": settings.ai_model,
        "provider": "gemini",
    }


@router.post("/chat")
async def chat(payload: ChatRequest):
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured.",
        )

    agent = AGENTS[payload.agent_id]

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

    prompt = (
        f"{_build_context(tasks, notes)}\n\n"
        f"Selected agent: {agent['name']}\n"
        f"Agent role: {agent['description']}\n\n"
        f"User request:\n{payload.message}"
    )

    try:
        answer = await asyncio.to_thread(_generate, prompt, payload.agent_id)
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
        "agent_id": payload.agent_id,
        "agent_name": agent["name"],
        "model": settings.ai_model,
        "provider": "gemini",
        "actions": [],
    }
