from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    plan: str
    max_agents: int
    max_members: int
    monthly_token_limit: int
    monthly_task_limit: int
    settings: dict
    is_active: bool
    member_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrgMemberResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrgInviteCreate(BaseModel):
    email: str
    role: str = "member"


class OrgInviteResponse(BaseModel):
    id: int
    email: str
    role: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
