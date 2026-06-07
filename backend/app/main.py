from fastapi import FastAPI

from app.config.settings import settings
from app.workspaces.router import router as workspaces_router

app = FastAPI(title=settings.app_name, version=settings.version)
app.include_router(workspaces_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


