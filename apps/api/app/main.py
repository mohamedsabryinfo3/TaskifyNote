from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.routes.health import router as health_router
from .api.routes.tasks import router as tasks_router
from .api.routes.notes import router as notes_router
from .api.routes.search import router as search_router
from .api.routes.ingest import router as ingest_router
from .api.routes.ai import router as ai_router

app = FastAPI(title="TaskifyNote API", version="0.7.5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(notes_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(ingest_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"name": "TaskifyNote", "version": "0.7.5", "status": "ok"}
