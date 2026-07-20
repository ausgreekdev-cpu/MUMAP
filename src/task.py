from enum import Enum
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Status of a task throughout its lifecycle."""
    PENDING = "pending"          # Waiting to be assigned
    ASSIGNED = "assigned"        # Assigned to an agent
    IN_PROGRESS = "in_progress"  # Being worked on
    COMPLETED = "completed"      # Done!
    FAILED = "failed"            # Something went wrong
    CANCELLED = "cancelled"      # No longer needed


class Task(BaseModel):
    """A unit of work that needs to be done by an agent.

    Tasks are the main currency of the platform. The orchestrator
    creates tasks and assigns them to the right agents.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    created_by: str = "orchestrator"
    required_capabilities: list[str] = Field(default_factory=list)
    input_data: dict = Field(default_factory=dict)
    output_data: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def complete(self, output: dict) -> None:
        """Mark this task as completed with its results."""
        self.status = TaskStatus.COMPLETED
        self.output_data = output
        self.completed_at = datetime.now()
    
    def fail(self, error: str) -> None:
        """Mark this task as failed with an error message."""
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now()
    
    def __str__(self) -> str:
        return f"[{self.priority.value}] {self.name} ({self.status.value})"
