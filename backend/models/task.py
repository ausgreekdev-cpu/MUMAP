from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import Base


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
    COMPOSITE = "composite"
    PIPELINE = "pipeline"
    PARALLEL = "parallel"


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    task_type = Column(String(20), default=TaskType.SIMPLE)
    
    status = Column(String(20), default=TaskStatus.PENDING, index=True)
    priority = Column(String(20), default=TaskPriority.NORMAL, index=True)
    
    required_capabilities = Column(JSON, default=list)
    required_role = Column(String(50), nullable=True)
    tags = Column(JSON, default=list)
    
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    task_metadata = Column("metadata", JSON, default=dict)
    
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    timeout_seconds = Column(Integer, default=3600)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    assigned_to = Column(Integer, ForeignKey("agents.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    tokens_used = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
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
    __tablename__ = "task_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    depends_on_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    dependency_type = Column(String(20), default="finish_to_start")
    
    task = relationship("Task", back_populates="dependencies", foreign_keys=[task_id])
    dependent_task = relationship("Task", back_populates="dependents", foreign_keys=[depends_on_task_id])


class TaskLog(Base):
    __tablename__ = "task_logs"
    __table_args__ = (
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    
    level = Column(String(10), default="INFO")
    event = Column(String(50), nullable=False)
    message = Column(Text, default="")
    
    data = Column(JSON, default=dict)
    
    duration_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    task = relationship("Task", back_populates="logs")


class TaskResult(Base):
    __tablename__ = "task_results"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    input_hash = Column(String(64), nullable=False, index=True)
    result_hash = Column(String(64), nullable=False)
    
    result_data = Column(JSON, nullable=False)
    
    hit_count = Column(Integer, default=0)
    last_hit_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
