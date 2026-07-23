from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class TaskBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    priority: str = "normal"
    required_capabilities: List[str] = []
    input_data: dict = {}
    task_type: str = "simple"
    max_retries: int = Field(3, ge=0, le=10)
    timeout_seconds: int = Field(3600, ge=30, le=86400)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = None
    required_capabilities: Optional[List[str]] = None
    input_data: Optional[dict] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=30, le=86400)


class TaskResponse(BaseModel):
    id: int
    name: str
    description: str
    status: str
    priority: str
    assigned_to: Optional[int]
    required_capabilities: List[str]
    input_data: dict
    output_data: dict
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


class TaskLogResponse(BaseModel):
    id: int
    task_id: int
    agent_id: Optional[int]
    event: str
    message: str
    data: dict
    created_at: datetime

    class Config:
        from_attributes = True


class TaskAssignRequest(BaseModel):
    agent_id: int
