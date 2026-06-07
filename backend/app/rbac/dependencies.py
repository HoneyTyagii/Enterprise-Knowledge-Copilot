from fastapi import Depends

from app.multitenancy.dependencies import require_tenant_context
from app.multitenancy.context import TenantContext
from app.rbac.checks import authorize


def require_permission(action: str, resource: str):
    def _dep(ctx: TenantContext = Depends(require_tenant_context)):
        authorize(ctx, action, resource)
        return ctx

    return _dep

