from fastapi import FastAPI

try:
    from app.main import app as taskifynote_app
    app = taskifynote_app
except Exception as exc:
    app = FastAPI(title="TaskifyNote API bootstrap")

    @app.get("/")
    async def bootstrap_error():
        return {
            "name": "TaskifyNote",
            "status": "bootstrap_error",
            "error_type": exc.__class__.__name__,
        }

    @app.get("/api/v1/health")
    async def bootstrap_health():
        return {
            "name": "TaskifyNote",
            "status": "bootstrap_error",
            "error_type": exc.__class__.__name__,
        }
