from typing import Iterable

from fastapi import HTTPException, status

from app.multitenancy.context import TenantContext
from app.rbac.policy import DEFAULT_POLICY, Permission


def _matches(request_action: str, request_resource: str, perm: Permission) -> bool:
    action_ok = perm.action == "*" or perm.action == request_action
    resource_ok = perm.resource == "*" or perm.resource == request_resource
    return action_ok and resource_ok


def authorize(ctx: TenantContext, action: str, resource: str, *, role_policy: dict[str, list[Permission]] = DEFAULT_POLICY) -> None:
    perms: Iterable[Permission] = role_policy.get(ctx.role, [])
    if any(_matches(action, resource, perm) for perm in perms):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Forbidden: role={ctx.role} cannot {action} {resource}",
    )

