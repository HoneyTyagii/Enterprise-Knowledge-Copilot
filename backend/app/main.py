from fastapi import FastAPI

from app.config.settings import settings
from app.observability.setup import setup_observability
from app.workspaces.router import router as workspaces_router
from app.ingestion.router import router as ingestion_router
from app.auth.router import router as auth_router
from app.query.router import router as query_router

app = FastAPI(title=settings.app_name, version=settings.version)

setup_observability(app)

app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(ingestion_router)
app.include_router(query_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}



