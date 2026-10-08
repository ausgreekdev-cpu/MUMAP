from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class TemplateResponse(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    category: str
    author: str
    price_label: str
    price_cents: int
    rating: float
    installs_count: int
    icon_key: str
    capabilities: list[str]
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    is_public: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TemplateListResponse(BaseModel):
    templates: list[TemplateResponse]
    total: int


class InstallationResponse(BaseModel):
    id: int
    template_id: int
    agent_id: Optional[int] = None
    installed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InstallationListResponse(BaseModel):
    installations: list[InstallationResponse]
    total: int


class InstallRequest(BaseModel):
    name: Optional[str] = None


class InstallResponse(BaseModel):
    installation: InstallationResponse
    template: TemplateResponse
    agent_id: int
    agent_name: str
