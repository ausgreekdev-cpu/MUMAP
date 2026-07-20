from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base


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
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Basic info
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, default="")
    role = Column(String(50), default=AgentRole.WORKER)
    
    # Capabilities and skills
    capabilities = Column(JSON, default=list)  # ["math", "analysis", "coding"]
    skills = Column(JSON, default=dict)  # {"python": 0.9, "javascript": 0.7}
    system_prompt = Column(Text, nullable=True)  # For AI-powered agents
    
    # Configuration
    config = Column(JSON, default=dict)  # Agent-specific configuration
    max_concurrent_tasks = Column(Integer, default=1)
    timeout_seconds = Column(Integer, default=300)  # 5 minutes
    
    # Status and health
    status = Column(String(20), default=AgentStatus.IDLE)
    health_score = Column(Float, default=1.0)  # 0.0 to 1.0
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    # Current state
    current_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Statistics
    completed_tasks_count = Column(Integer, default=0)
    failed_tasks_count = Column(Integer, default=0)
    total_processing_time = Column(Integer, default=0)  # seconds
    average_task_time = Column(Float, default=0.0)
    
    # Scheduling
    is_active = Column(Boolean, default=True)
    schedule = Column(JSON, nullable=True)  # Cron-like schedule
    priority = Column(Integer, default=0)  # Higher = preferred
    
    # Model configuration (for AI agents)
    model_provider = Column(String(50), nullable=True)  # openai, anthropic, etc.
    model_name = Column(String(100), nullable=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
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
    """Time-series metrics for agents."""
    __tablename__ = "agent_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    # Metric data
    metric_type = Column(String(50), nullable=False)  # response_time, error_rate, etc.
    value = Column(Float, nullable=False)
    metric_metadata = Column("metadata", JSON, default=dict)
    
    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="metrics")
