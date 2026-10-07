from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/ai", tags=["AI"])

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(payload: ChatRequest):
    return {
      "message": "AI provider is ready. Configure GEMINI_API_KEY on Vercel or Ollama locally.",
      "input": payload.message,
      "actions": []
    }
