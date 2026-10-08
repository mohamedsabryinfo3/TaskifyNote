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



def _extract_youtube_id(url: str) -> str | None:
    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if path == "watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if path.startswith("shorts/"):
            return path.split("/", 1)[1].split("/")[0]
        if path.startswith("embed/"):
            return path.split("/", 1)[1].split("/")[0]
    if host == "youtu.be":
        return path.split("/")[0]

    return None


def _fetch_youtube_transcript(video_id: str) -> tuple[str, str]:
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()

    errors: list[Exception] = []
    for languages in (["ar", "en"], ["en"], ["ar"]):
        try:
            transcript = api.fetch(video_id, languages=languages)
            text = " ".join(snippet.text.strip() for snippet in transcript if snippet.text.strip())
            if text:
                return text, transcript.language_code
        except Exception as exc:
            errors.append(exc)

    raise RuntimeError(
        "No usable YouTube transcript was available."
        + (f" {errors[-1].__class__.__name__}" if errors else "")
    )


def _generate_tasks_from_transcript(transcript: str, source_url: str) -> list[dict]:
    import json

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = f"""
You are the Task Manager agent inside TaskifyNote.

Turn the following YouTube lesson transcript into 3 to 7 concrete learning tasks.
Each task must be something the user can actually do, not a vague goal.
Prefer a progression: watch/understand, practice, review, and apply.
Do not invent topics that are not supported by the transcript.

Return ONLY valid JSON in this shape:
[
  {{
    "title": "short task title",
    "description": "one-sentence actionable description",
    "priority": 0
  }}
]

Use priority 2 for essential tasks, 1 for useful tasks, and 0 for optional tasks.
Source URL: {source_url}

Transcript:
{transcript[:30000]}
"""

    response = client.models.generate_content(
        model=settings.ai_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=1000,
        ),
    )

    raw = (response.text or "").strip()
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise ValueError("AI task output was not a list")

    cleaned: list[dict] = []
    for item in parsed[:7]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        description = str(item.get("description", "")).strip()
        priority = int(item.get("priority", 0))
        if title:
            cleaned.append(
                {
                    "title": title[:500],
                    "description": description[:2000],
                    "priority": max(0, min(priority, 2)),
                }
            )

    if not cleaned:
        raise ValueError("AI returned no usable tasks")
    return cleaned

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


@router.post("/tasks-from-url")
async def tasks_from_url(payload: dict):
    url = str(payload.get("url", "")).strip()
    if not url:
        raise HTTPException(status_code=400, detail="A YouTube URL is required.")

    video_id = _extract_youtube_id(url)
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="This action currently supports public YouTube video URLs.",
        )

    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured.")

    try:
        transcript, language = await asyncio.to_thread(
            _fetch_youtube_transcript, video_id
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read the YouTube transcript: {exc.__class__.__name__}",
        ) from exc

    try:
        task_specs = await asyncio.to_thread(
            _generate_tasks_from_transcript, transcript, url
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI task generation failed: {exc.__class__.__name__}",
        ) from exc

    try:
        factory = _get_session_factory()
        async with factory() as db:
            created = []
            for spec in task_specs:
                task = Task(
                    title=spec["title"],
                    description=spec["description"],
                    priority=spec["priority"],
                    status="todo",
                )
                db.add(task)
                created.append(task)

            await db.commit()
            for task in created:
                await db.refresh(task)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Could not save generated tasks: {exc.__class__.__name__}",
        ) from exc

    return {
        "status": "created",
        "video_id": video_id,
        "source_url": url,
        "transcript_language": language,
        "count": len(created),
        "tasks": [
            {
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "status": task.status,
            }
            for task in created
        ],
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
