from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AgentBase(BaseModel):
    name: str
    description: str = ""
    role: str = "worker"
    capabilities: list[str] = []
    max_concurrent_tasks: int = 1


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    capabilities: Optional[list[str]] = None
    max_concurrent_tasks: Optional[int] = None


class AgentResponse(AgentBase):
    id: int
    status: str
    current_task_id: Optional[int] = None
    completed_tasks_count: int
    failed_tasks_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
    total: int
