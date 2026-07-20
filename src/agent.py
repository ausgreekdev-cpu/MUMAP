from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from .message import Message, MessageType
from .task import Task, TaskStatus


class AgentRole(str, Enum):
    """Predefined roles for agents."""
    WORKER = "worker"
    COORDINATOR = "coordinator"
    ANALYZER = "analyzer"
    RESEARCHER = "researcher"
    CUSTOM = "custom"


class AgentStatus(str, Enum):
    """Current status of an agent."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    name: str
    role: AgentRole = AgentRole.WORKER
    capabilities: list[str] = Field(default_factory=list)
    max_concurrent_tasks: int = 1


class Agent(ABC):
    """Base class for all agents in the platform.
    
    To create your own agent, subclass this and implement:
    - process_task(): How this agent handles work
    - handle_message(): How this agent responds to messages
    
    Example:
        class MyAgent(Agent):
            def process_task(self, task):
                # Do the work
                return {"result": "done"}
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.id = str(uuid.uuid4())[:8]
        self.status = AgentStatus.IDLE
        self.current_task: Task | None = None
        self.completed_tasks: list[Task] = []
        self._message_handlers: dict[MessageType, Callable] = {}
        self._message_queue: list[Message] = []
        self._created_at = datetime.now()
        
        # Register default message handlers
        self._register_default_handlers()
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def role(self) -> AgentRole:
        return self.config.role
    
    @property
    def capabilities(self) -> list[str]:
        return self.config.capabilities
    
    def can_handle(self, task: Task) -> bool:
        """Check if this agent can handle a given task.
        
        Returns True if the agent has all required capabilities.
        """
        if not task.required_capabilities:
            return True
        return all(cap in self.capabilities for cap in task.required_capabilities)
    
    @abstractmethod
    def process_task(self, task: Task) -> dict[str, Any]:
        """Process a task and return results.
        
        This is where you implement your agent's logic.
        
        Args:
            task: The task to process
            
        Returns:
            Dictionary with task results
        """
        pass
    
    def handle_message(self, message: Message) -> Message | None:
        """Handle an incoming message.
        
        Override this to customize how your agent responds to messages.
        """
        if message.type == MessageType.TASK_ASSIGN:
            return self._handle_task_assignment(message)
        elif message.type == MessageType.QUERY:
            return self._handle_query(message)
        elif message.type == MessageType.BROADCAST:
            return self._handle_broadcast(message)
        return None
    
    def _handle_task_assignment(self, message: Message) -> Message:
        """Handle being assigned a new task."""
        task_data = message.content
        task = Task(**task_data) if isinstance(task_data, dict) else task_data
        
        if self.status == AgentStatus.BUSY:
            return Message(
                sender=self.id,
                receiver=message.sender,
                type=MessageType.STATUS,
                content={"status": "busy", "message": "Already working on a task"}
            )
        
        self.current_task = task
        self.status = AgentStatus.BUSY
        
        try:
            result = self.process_task(task)
            task.complete(result)
            self.completed_tasks.append(task)
            self.current_task = None
            self.status = AgentStatus.IDLE
            
            return Message(
                sender=self.id,
                receiver=message.sender,
                type=MessageType.TASK_RESULT,
                content={"task_id": task.id, "result": result}
            )
        except Exception as e:
            task.fail(str(e))
            self.status = AgentStatus.ERROR
            return Message(
                sender=self.id,
                receiver=message.sender,
                type=MessageType.ERROR,
                content={"task_id": task.id, "error": str(e)}
            )
    
    def _handle_query(self, message: Message) -> Message:
        """Handle a query about agent status."""
        return Message(
            sender=self.id,
            receiver=message.sender,
            type=MessageType.RESPONSE,
            content={
                "status": self.status.value,
                "current_task": self.current_task.id if self.current_task else None,
                "completed_count": len(self.completed_tasks),
            }
        )
    
    def _handle_broadcast(self, message: Message) -> None:
        """Handle a broadcast message (just log it)."""
        pass
    
    def _register_default_handlers(self) -> None:
        """Register default message type handlers."""
        self._message_handlers = {
            MessageType.TASK_ASSIGN: self._handle_task_assignment,
            MessageType.QUERY: self._handle_query,
            MessageType.BROADCAST: self._handle_broadcast,
        }
    
    def receive_message(self, message: Message) -> Message | None:
        """Add a message to queue and process it."""
        self._message_queue.append(message)
        return self.handle_message(message)
    
    def __repr__(self) -> str:
        return f"Agent({self.name}, role={self.role.value}, status={self.status.value})"
