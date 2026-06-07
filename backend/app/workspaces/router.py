from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Workspace, WorkspaceMember
from app.db.session import get_db
from app.multitenancy.dependencies import require_tenant_context
from app.multitenancy.context import TenantContext
from app.rbac.dependencies import require_permission
from app.workspaces.schemas import (
    MemberAdd,
    MemberOut,
    MemberUpdate,
    WorkspaceCreate,
    WorkspaceOut,
    WorkspaceUpdate,
)
from app.workspaces.service import (
    add_member,
    create_workspace,
    delete_workspace,
    get_workspace,
    list_members,
    list_workspaces,
    remove_member,
    update_member_role,
    update_workspace,
)

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


def _ensure_membership_in_workspace(db: Session, ctx: TenantContext, workspace_id: int) -> WorkspaceMember:
    row = db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == ctx.actor_user_id,
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace",
        )
    return row


def _require_admin_role(ctx: TenantContext, member: WorkspaceMember) -> None:
    if member.role not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this operation",
        )


@router.post("/", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
async def create_workspace_endpoint(
    payload: WorkspaceCreate,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> WorkspaceOut:
    workspace = create_workspace(db, org_id=ctx.tenant_id, name=payload.name)
    add_member(db, workspace_id=workspace.id, user_id=ctx.actor_user_id, role="owner")
    return WorkspaceOut.model_validate(workspace)


@router.get("/", response_model=List[WorkspaceOut])
async def list_workspaces_endpoint(
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> List[WorkspaceOut]:
    workspaces = list_workspaces(db, org_id=ctx.tenant_id)
    return [WorkspaceOut.model_validate(w) for w in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace_endpoint(
    workspace_id: int,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> WorkspaceOut:
    workspace = get_workspace(db, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace is outside your organization")
    _ensure_membership_in_workspace(db, ctx, workspace_id)
    return WorkspaceOut.model_validate(workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceOut)
async def update_workspace_endpoint(
    workspace_id: int,
    payload: WorkspaceUpdate,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> WorkspaceOut:
    workspace = get_workspace(db, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace is outside your organization")
    membership = _ensure_membership_in_workspace(db, ctx, workspace_id)
    _require_admin_role(ctx, membership)
    updated = update_workspace(
        db,
        workspace_id,
        name=payload.name,
        status=payload.status,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return WorkspaceOut.model_validate(updated)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace_endpoint(
    workspace_id: int,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    workspace = get_workspace(db, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace is outside your organization")
    membership = _ensure_membership_in_workspace(db, ctx, workspace_id)
    _require_admin_role(ctx, membership)
    if not delete_workspace(db, workspace_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")


@router.get("/{workspace_id}/members", response_model=List[MemberOut])
async def list_members_endpoint(
    workspace_id: int,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> List[MemberOut]:
    workspace = get_workspace(db, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace is outside your organization")
    _ensure_membership_in_workspace(db, ctx, workspace_id)
    members = list_members(db, workspace_id)
    return [MemberOut.model_validate(m) for m in members]


@router.post(
    "/{workspace_id}/members",
    response_model=MemberOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_member_endpoint(
    workspace_id: int,
    payload: MemberAdd,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> MemberOut:
    workspace = get_workspace(db, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace is outside your organization")
    membership = _ensure_membership_in_workspace(db, ctx, workspace_id)
    _require_admin_role(ctx, membership)
    user = get_user(db, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    member = add_member(db, workspace_id, payload.user_id, payload.role)
    return MemberOut.model_validate(member)


@router.patch("/{workspace_id}/members/{user_id}", response_model=MemberOut)
async def update_member_endpoint(
    workspace_id: int,
    user_id: int,
    payload: MemberUpdate,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> MemberOut:
    workspace = get_workspace(db, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace is outside your organization")
    membership = _ensure_membership_in_workspace(db, ctx, workspace_id)
    _require_admin_role(ctx, membership)

    target = get_user(db, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    member = update_member_role(db, workspace_id, user_id, payload.role)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    return MemberOut.model_validate(member)


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_endpoint(
    workspace_id: int,
    user_id: int,
    ctx: TenantContext = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    workspace = get_workspace(db, workspace_id)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    if workspace.organization_id != ctx.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace is outside your organization")
    membership = _ensure_membership_in_workspace(db, ctx, workspace_id)
    _require_admin_role(ctx, membership)

    targets = db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    ).scalar_one_or_none()
    if targets and targets.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the owner from the workspace",
        )

    if not remove_member(db, workspace_id, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
