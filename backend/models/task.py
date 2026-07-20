from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TaskType(str, enum.Enum):
    SIMPLE = "simple"
    COMPOSITE = "composite"  # Parent of subtasks
    PIPELINE = "pipeline"    # Sequential execution
    PARALLEL = "parallel"    # Parallel execution


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    task_type = Column(String(20), default=TaskType.SIMPLE)
    
    # Status and priority
    status = Column(String(20), default=TaskStatus.PENDING)
    priority = Column(String(20), default=TaskPriority.NORMAL)
    
    # Requirements
    required_capabilities = Column(JSON, default=list)
    required_role = Column(String(50), nullable=True)
    tags = Column(JSON, default=list)
    
    # Data
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    task_metadata = Column("metadata", JSON, default=dict)
    
    # Execution
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    timeout_seconds = Column(Integer, default=3600)  # 1 hour
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey("agents.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    # Parent-child relationships (for composite tasks)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Cost tracking
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    tokens_used = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="tasks")
    organization = relationship("Organization", back_populates="tasks")
    agent = relationship("Agent", back_populates="tasks", foreign_keys=[assigned_to])
    subtasks = relationship("Task", backref="parent_task", remote_side=[id])
    logs = relationship("TaskLog", back_populates="task")
    dependencies = relationship("TaskDependency", back_populates="task", foreign_keys="TaskDependency.task_id")
    dependents = relationship("TaskDependency", back_populates="dependent_task", foreign_keys="TaskDependency.depends_on_task_id")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "required_capabilities": self.required_capabilities,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class TaskDependency(Base):
    """Task dependencies for DAG execution."""
    __tablename__ = "task_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    depends_on_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Relationship type
    dependency_type = Column(String(20), default="finish_to_start")  # finish_to_start, data_dependency
    
    # Relationships
    task = relationship("Task", back_populates="dependencies", foreign_keys=[task_id])
    dependent_task = relationship("Task", back_populates="dependents", foreign_keys=[depends_on_task_id])


class TaskLog(Base):
    """Detailed execution logs for tasks."""
    __tablename__ = "task_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    
    # Log details
    level = Column(String(10), default="INFO")  # DEBUG, INFO, WARNING, ERROR
    event = Column(String(50), nullable=False)
    message = Column(Text, default="")
    
    # Structured data
    data = Column(JSON, default=dict)
    
    # Performance
    duration_ms = Column(Integer, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="logs")


class TaskResult(Base):
    """Cached task results for reuse."""
    __tablename__ = "task_results"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Result hash for deduplication
    input_hash = Column(String(64), nullable=False, index=True)
    result_hash = Column(String(64), nullable=False)
    
    # Cached result
    result_data = Column(JSON, nullable=False)
    
    # Usage stats
    hit_count = Column(Integer, default=0)
    last_hit_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
