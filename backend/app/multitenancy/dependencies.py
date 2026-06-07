from fastapi import Depends, HTTPException, Request, status

from app.auth.dependencies import require_jwt_credentials
from app.multitenancy.context import TenantContext


def _coerce_int(name: str, value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {name}")


def require_tenant_context(request: Request, token_payload=Depends(require_jwt_credentials)) -> TenantContext:
    # Expected JWT claims (to be enforced in later commits)
    # token_payload may contain: tenant_id, workspace_id, role, userId, email
    tenant_id = token_payload.get("tenant_id")
    workspace_id = token_payload.get("workspace_id")
    role = token_payload.get("role")
    user_id = token_payload.get("userId") or token_payload.get("user_id")
    email = token_payload.get("email")

    if tenant_id is None or workspace_id is None or role is None or user_id is None or email is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing tenant/workspace claims")

    request_id = request.headers.get("x-request-id")

    return TenantContext(
        tenant_id=_coerce_int("tenant_id", tenant_id),
        workspace_id=_coerce_int("workspace_id", workspace_id),
        role=str(role),
        actor_user_id=_coerce_int("user_id", user_id),
        actor_email=str(email),
        request_id=request_id,
    )

