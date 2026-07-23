from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class AgentRole(str, Enum):
    WORKER = "worker"
    COORDINATOR = "coordinator"
    ANALYZER = "analyzer"
    RESEARCHER = "researcher"
    WRITER = "writer"
    CODER = "coder"
    CUSTOM = "custom"


@dataclass
class Agent:
    name: str
    owner_id: int
    id: Optional[int] = None
    description: str = ""
    role: AgentRole = AgentRole.WORKER
    capabilities: list[str] = field(default_factory=list)
    skills: dict[str, float] = field(default_factory=dict)
    system_prompt: Optional[str] = None
    config: dict = field(default_factory=dict)
    max_concurrent_tasks: int = 1
    timeout_seconds: int = 300
    status: AgentStatus = AgentStatus.IDLE
    health_score: float = 1.0
    error_count: int = 0
    last_error: Optional[str] = None
    current_task_id: Optional[int] = None
    completed_tasks_count: int = 0
    failed_tasks_count: int = 0
    total_processing_time: int = 0
    average_task_time: float = 0.0
    is_active: bool = True
    priority: int = 0
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    organization_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None

    def can_handle(self, required_capabilities: list[str]) -> bool:
        if not required_capabilities:
            return True
        return all(cap in self.capabilities for cap in required_capabilities)

    def assign_task(self, task_id: int) -> None:
        if self.status != AgentStatus.IDLE:
            raise ValueError(f"Agent {self.name} is not available (status: {self.status})")
        if self.current_task_id is not None:
            raise ValueError(f"Agent {self.name} already has an assigned task")
        self.status = AgentStatus.BUSY
        self.current_task_id = task_id
        self.last_active_at = datetime.utcnow()

    def complete_task(self, duration_seconds: int = 0) -> None:
        self.status = AgentStatus.IDLE
        self.current_task_id = None
        self.completed_tasks_count += 1
        self.total_processing_time += duration_seconds
        if self.completed_tasks_count > 0:
            self.average_task_time = self.total_processing_time / self.completed_tasks_count
        self.last_active_at = datetime.utcnow()

    def fail_task(self, error: str) -> None:
        self.status = AgentStatus.ERROR
        self.current_task_id = None
        self.failed_tasks_count += 1
        self.error_count += 1
        self.last_error = error
        self.last_active_at = datetime.utcnow()

    def reset_error(self) -> None:
        if self.status == AgentStatus.ERROR:
            self.status = AgentStatus.IDLE
            self.last_error = None

    def deactivate(self) -> None:
        self.is_active = False
        self.status = AgentStatus.OFFLINE

    def activate(self) -> None:
        self.is_active = True
        self.status = AgentStatus.IDLE

    @property
    def success_rate(self) -> float:
        total = self.completed_tasks_count + self.failed_tasks_count
        if total == 0:
            return 1.0
        return self.completed_tasks_count / total

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "status": self.status.value,
            "health_score": self.health_score,
            "completed_tasks_count": self.completed_tasks_count,
            "failed_tasks_count": self.failed_tasks_count,
            "average_task_time": self.average_task_time,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
