from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TaskType(str, Enum):
    SIMPLE = "simple"
    COMPOSITE = "composite"
    PIPELINE = "pipeline"
    PARALLEL = "parallel"


class InvalidStateTransition(Exception):
    pass


@dataclass
class Task:
    name: str
    id: Optional[int] = None
    creator_id: Optional[int] = None
    organization_id: Optional[int] = None
    description: str = ""
    task_type: TaskType = TaskType.SIMPLE
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    required_capabilities: list[str] = field(default_factory=list)
    required_role: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    input_data: dict = field(default_factory=dict)
    output_data: dict = field(default_factory=dict)
    task_metadata: dict = field(default_factory=dict)
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: int = 3600
    last_retry_at: Optional[datetime] = None
    assigned_to: Optional[int] = None
    assigned_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    parent_task_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    tokens_used: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def assign(self, agent_id: int) -> None:
        if self.status not in (TaskStatus.PENDING, TaskStatus.QUEUED):
            raise InvalidStateTransition(
                f"Cannot assign task in {self.status.value} status"
            )
        self.status = TaskStatus.ASSIGNED
        self.assigned_to = agent_id
        self.assigned_at = datetime.utcnow()

    def start(self) -> None:
        if self.status != TaskStatus.ASSIGNED:
            raise InvalidStateTransition(
                f"Cannot start task in {self.status.value} status"
            )
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()

    def complete(self, output: dict) -> None:
        if self.status != TaskStatus.IN_PROGRESS:
            raise InvalidStateTransition(
                f"Cannot complete task in {self.status.value} status"
            )
        self.status = TaskStatus.COMPLETED
        self.output_data = output
        self.completed_at = datetime.utcnow()

    def fail(self, error: str) -> None:
        if self.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            raise InvalidStateTransition(
                f"Cannot fail task in {self.status.value} status"
            )
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()

    def cancel(self) -> None:
        if self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            raise InvalidStateTransition(
                f"Cannot cancel task in {self.status.value} status"
            )
        self.status = TaskStatus.CANCELLED

    def retry(self) -> bool:
        if self.retry_count >= self.max_retries:
            return False
        if self.status != TaskStatus.FAILED:
            raise InvalidStateTransition(
                f"Cannot retry task in {self.status.value} status"
            )
        self.status = TaskStatus.RETRYING
        self.retry_count += 1
        self.last_retry_at = datetime.utcnow()
        self.error_message = None
        return True

    def timeout(self) -> None:
        if self.status == TaskStatus.IN_PROGRESS:
            self.status = TaskStatus.TIMEOUT
            self.error_message = "Task timed out"
            self.completed_at = datetime.utcnow()

    @property
    def can_retry(self) -> bool:
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        )

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "assigned_to": self.assigned_to,
            "required_capabilities": self.required_capabilities,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
