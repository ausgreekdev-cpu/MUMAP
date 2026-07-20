from enum import Enum
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


class MessageType(str, Enum):
    """Types of messages agents can send to each other."""
    TASK_ASSIGN = "task_assign"
    TASK_RESULT = "task_result"
    QUERY = "query"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    STATUS = "status"
    ERROR = "error"


class Message(BaseModel):
    """A message that agents send to each other.

    This is how agents communicate in the platform. Each message has:
    - A sender (who sent it)
    - A receiver (who should get it)
    - A type (what kind of message it is)
    - Content (the actual data)
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender: str
    receiver: str
    type: MessageType
    content: Any
    metadata: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        return f"[{self.type.value}] {self.sender} -> {self.receiver}: {str(self.content)[:50]}"
