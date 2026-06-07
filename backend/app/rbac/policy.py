from dataclasses import dataclass


@dataclass(frozen=True)
class Permission:
    action: str
    resource: str


# Minimal default policy map. Expand per your domain.
# role -> list of permissions patterns
DEFAULT_POLICY: dict[str, list[Permission]] = {
    "owner": [Permission(action="*", resource="*")],
    "admin": [Permission(action="*", resource="*")],
    "member": [
        Permission(action="read", resource="document"),
        Permission(action="query", resource="document"),
        Permission(action="ingest", resource="document"),
    ],
    "viewer": [
        Permission(action="read", resource="document"),
        Permission(action="query", resource="document"),
    ],
}

