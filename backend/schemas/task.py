from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskBase(BaseModel):
    name: str
    description: str = ""
    priority: str = "medium"
    required_capabilities: list[str] = []
    input_data: dict = {}


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    required_capabilities: Optional[list[str]] = None
    input_data: Optional[dict] = None


class TaskResponse(TaskBase):
    id: int
    status: str
    output_data: dict
    error_message: Optional[str] = None
    assigned_to: Optional[int] = None
    creator_id: Optional[int] = None
    created_at: datetime
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int


class TaskLogResponse(BaseModel):
    id: int
    task_id: int
    event: str
    message: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class TaskAssignRequest(BaseModel):
    agent_id: int
