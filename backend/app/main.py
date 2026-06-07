from fastapi import FastAPI

from app.config.settings import settings
from app.workspaces.router import router as workspaces_router
from app.ingestion.router import router as ingestion_router

app = FastAPI(title=settings.app_name, version=settings.version)
app.include_router(workspaces_router)
app.include_router(ingestion_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


