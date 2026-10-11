from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WebhookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=500)
    events: list[str] = Field(min_length=1)
    secret: Optional[str] = Field(default=None, max_length=255)
    headers: Optional[dict[str, str]] = None


class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    events: list[str]
    headers: dict
    is_active: bool
    secret_set: bool = False
    last_triggered_at: Optional[datetime] = None
    failure_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookCreated(WebhookResponse):
    secret: str
