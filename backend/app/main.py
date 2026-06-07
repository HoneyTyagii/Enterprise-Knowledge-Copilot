from fastapi import FastAPI

from .config.settings import settings

app = FastAPI(title=settings.app_name, version=settings.version)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


