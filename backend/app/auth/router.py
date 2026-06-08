from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.auth.jwt import create_access_token
from app.config.settings import settings
from app.db.models import Organization, User, Workspace, WorkspaceMember
from app.db.session import get_db
from app.multitenancy.context import TenantContext
from app.rbac.policy import DEFAULT_POLICY
from app.rbac.checks import authorize

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    email: str,
    password: str,
    organization_name: str,
    workspace_name: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    org = Organization(name=organization_name)
    db.add(org)
    db.commit()
    db.refresh(org)

    user = User(email=email, password_hash=_hash_password(password), password_salt="")
    db.add(user)
    db.commit()
    db.refresh(user)

    workspace = Workspace(organization_id=org.id, name=workspace_name)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
    db.commit()

    token = create_access_token(
        payload={
            "tenant_id": org.id,
            "workspace_id": workspace.id,
            "role": "owner",
            "userId": user.id,
            "email": user.email,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant_id": org.id,
        "workspace_id": workspace.id,
        "role": "owner",
        "user_id": user.id,
        "email": user.email,
    }


@router.post("/login")
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not _verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    membership = db.execute(
        select(WorkspaceMember).where(WorkspaceMember.user_id == user.id)
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No workspace membership")

    workspace = db.execute(select(Workspace).where(Workspace.id == membership.workspace_id)).scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace not found")

    token = create_access_token(
        payload={
            "tenant_id": workspace.organization_id,
            "workspace_id": workspace.id,
            "role": membership.role,
            "userId": user.id,
            "email": user.email,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant_id": workspace.organization_id,
        "workspace_id": workspace.id,
        "role": membership.role,
        "user_id": user.id,
        "email": user.email,
    }
