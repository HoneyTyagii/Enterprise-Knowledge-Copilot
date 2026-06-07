from dataclasses import dataclass
from typing import Optional


@dataclass
class TenantContext:
    tenant_id: int
    workspace_id: int
    role: str
    actor_user_id: int
    actor_email: str
    request_id: Optional[str] = None

