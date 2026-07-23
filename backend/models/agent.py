from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import Base


class AgentStatus(str, enum.Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class AgentRole(str, enum.Enum):
    WORKER = "worker"
    COORDINATOR = "coordinator"
    ANALYZER = "analyzer"
    RESEARCHER = "researcher"
    WRITER = "writer"
    CODER = "coder"
    CUSTOM = "custom"


class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = (
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, default="")
    role = Column(String(50), default=AgentRole.WORKER, index=True)
    
    capabilities = Column(JSON, default=list)
    skills = Column(JSON, default=dict)
    system_prompt = Column(Text, nullable=True)
    
    config = Column(JSON, default=dict)
    max_concurrent_tasks = Column(Integer, default=1)
    timeout_seconds = Column(Integer, default=300)
    
    status = Column(String(20), default=AgentStatus.IDLE, index=True)
    health_score = Column(Float, default=1.0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    current_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    completed_tasks_count = Column(Integer, default=0)
    failed_tasks_count = Column(Integer, default=0)
    total_processing_time = Column(Integer, default=0)
    average_task_time = Column(Float, default=0.0)
    
    is_active = Column(Boolean, default=True)
    schedule = Column(JSON, nullable=True)
    priority = Column(Integer, default=0)
    
    model_provider = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    
    owner = relationship("User", back_populates="agents")
    organization = relationship("Organization", back_populates="agents")
    tasks = relationship("Task", back_populates="agent", foreign_keys="Task.assigned_to")
    metrics = relationship("AgentMetric", back_populates="agent")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "role": self.role,
            "capabilities": self.capabilities,
            "status": self.status,
            "health_score": self.health_score,
            "completed_tasks_count": self.completed_tasks_count,
            "failed_tasks_count": self.failed_tasks_count,
            "average_task_time": self.average_task_time,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AgentMetric(Base):
    __tablename__ = "agent_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    metric_metadata = Column("metadata", JSON, default=dict)
    
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    agent = relationship("Agent", back_populates="metrics")
