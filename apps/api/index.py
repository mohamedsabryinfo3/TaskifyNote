from fastapi import FastAPI

try:
    from app.main import app as taskifynote_app
    app = taskifynote_app
except Exception as exc:
    error_type = exc.__class__.__name__
    error_message = str(exc)[:200]

    app = FastAPI(title="TaskifyNote API bootstrap")

    @app.get("/")
    async def bootstrap_error():
        return {
            "name": "TaskifyNote",
            "status": "bootstrap_error",
            "error_type": error_type,
            "message": error_message,
        }

    @app.get("/api/v1/health")
    async def bootstrap_health():
        return {
            "name": "TaskifyNote",
            "status": "bootstrap_error",
            "error_type": error_type,
            "message": error_message,
        }
