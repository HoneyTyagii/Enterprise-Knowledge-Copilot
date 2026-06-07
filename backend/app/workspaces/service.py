from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import User, Workspace, WorkspaceMember
from app.rbac.policy import DEFAULT_POLICY


VALID_ROLES = set(DEFAULT_POLICY.keys())


def create_workspace(db: Session, org_id: int, name: str) -> Workspace:
    workspace = Workspace(organization_id=org_id, name=name)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


def get_workspace(db: Session, workspace_id: int) -> Workspace | None:
    result = db.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()


def list_workspaces(db: Session, org_id: int) -> List[Workspace]:
    result = db.execute(select(Workspace).where(Workspace.organization_id == org_id))
    return list(result.scalars().all())


def update_workspace(db: Session, workspace_id: int, **kwargs) -> Workspace | None:
    workspace = get_workspace(db, workspace_id)
    if workspace is None:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(workspace, key, value)
    db.commit()
    db.refresh(workspace)
    return workspace


def delete_workspace(db: Session, workspace_id: int) -> bool:
    workspace = get_workspace(db, workspace_id)
    if workspace is None:
        return False
    db.delete(workspace)
    db.commit()
    return True


def get_user(db: Session, user_id: int) -> User | None:
    result = db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def add_member(db: Session, workspace_id: int, user_id: int, role: str) -> WorkspaceMember:
    member = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)
    db.add(member)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("User is already a member of this workspace")
    db.refresh(member)
    return member


def list_members(db: Session, workspace_id: int) -> List[WorkspaceMember]:
    result = db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id))
    return list(result.scalars().all())


def update_member_role(db: Session, workspace_id: int, user_id: int, role: str) -> WorkspaceMember | None:
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id,
    )
    member = db.execute(stmt).scalar_one_or_none()
    if member is None:
        return None
    member.role = role
    db.commit()
    db.refresh(member)
    return member


def remove_member(db: Session, workspace_id: int, user_id: int) -> bool:
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id,
    )
    member = db.execute(stmt).scalar_one_or_none()
    if member is None:
        return False
    db.delete(member)
    db.commit()
    return True
