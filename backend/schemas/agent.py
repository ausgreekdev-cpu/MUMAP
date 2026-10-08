from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

VALID_MODEL_PROVIDERS = ("openai", "anthropic", "ollama")


class AgentBase(BaseModel):
    name: str
    description: str = ""
    role: str = "worker"
    capabilities: list[str] = []
    max_concurrent_tasks: int = 1

    # LLM configuration (for AI-powered agents)
    model_provider: Optional[str] = Field(
        default=None, description=f"One of: {', '.join(VALID_MODEL_PROVIDERS)}"
    )
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    capabilities: Optional[list[str]] = None
    max_concurrent_tasks: Optional[int] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class AgentResponse(AgentBase):
    id: int
    status: str
    current_task_id: Optional[int] = None
    completed_tasks_count: int
    failed_tasks_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
    total: int
