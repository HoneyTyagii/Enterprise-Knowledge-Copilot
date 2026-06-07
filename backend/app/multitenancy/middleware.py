from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Attach request id if present/desired; used later for audit logs
        request.state.request_id = request.headers.get("x-request-id")
        response = await call_next(request)
        return response



