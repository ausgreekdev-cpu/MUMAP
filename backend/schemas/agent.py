from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    role: str = "worker"
    capabilities: List[str] = []
    max_concurrent_tasks: int = Field(1, ge=1, le=10)
    timeout_seconds: int = Field(300, ge=30, le=3600)
    organization_id: Optional[int] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=1, le=100000)


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    role: Optional[str] = None
    capabilities: Optional[List[str]] = None
    max_concurrent_tasks: Optional[int] = Field(None, ge=1, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=30, le=3600)
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=100000)
    system_prompt: Optional[str] = None


class AgentResponse(BaseModel):
    id: int
    name: str
    description: str
    role: str
    capabilities: List[str]
    status: str
    health_score: float
    completed_tasks_count: int
    failed_tasks_count: int
    average_task_time: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
