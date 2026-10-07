from fastapi import FastAPI

app = FastAPI(title="TaskifyNote API", version="0.7.8")


@app.get("/")
async def root():
    return {
        "name": "TaskifyNote",
        "version": "0.7.8",
        "status": "ok",
    }


@app.get("/api/v1/health")
async def health():
    return {
        "name": "TaskifyNote",
        "version": "0.7.8",
        "status": "ok",
    }
