from datetime import datetime
from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    status: str | None = Field(None, min_length=1, max_length=50)


class WorkspaceOut(BaseModel):
    id: int
    organization_id: int
    name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MemberAdd(BaseModel):
    user_id: int = Field(..., gt=0)
    role: str = Field(..., min_length=1, max_length=50)


class MemberUpdate(BaseModel):
    role: str = Field(..., min_length=1, max_length=50)


class MemberOut(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
