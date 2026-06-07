from typing import Any

from fastapi import APIRouter


def create_tenant_router(prefix: str = "/") -> APIRouter:
    router = APIRouter(prefix=prefix)
    return router

