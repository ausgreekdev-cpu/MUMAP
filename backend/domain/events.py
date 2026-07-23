from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Any, Optional
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class Event:
    type: str
    data: dict
    source: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


class EventTypes:
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    AGENT_STATUS_CHANGED = "agent.status_changed"
    AGENT_ASSIGNED = "agent.assigned"
    AGENT_TASK_COMPLETED = "agent.task_completed"
    AGENT_TASK_FAILED = "agent.task_failed"

    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_DELETED = "task.deleted"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"
    TASK_RETRYING = "task.retrying"

    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"

    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"

    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._async_handlers: dict[str, list[Callable]] = defaultdict(list)
        self._event_log: list[Event] = []
        self._max_log_size: int = 1000

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    def subscribe_async(self, event_type: str, handler: Callable) -> None:
        self._async_handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    async def publish(self, event: Event) -> list[Any]:
        results = []
        self._log_event(event)

        for handler in self._handlers.get(event.type, []):
            try:
                result = handler(event)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in sync handler for {event.type}: {e}")

        for handler in self._async_handlers.get(event.type, []):
            try:
                result = await handler(event)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in async handler for {event.type}: {e}")

        for handler in self._handlers.get("*", []):
            try:
                result = handler(event)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in wildcard handler for {event.type}: {e}")

        for handler in self._async_handlers.get("*", []):
            try:
                result = await handler(event)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in async wildcard handler for {event.type}: {e}")

        return results

    def _log_event(self, event: Event) -> None:
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]

    def get_event_log(self, event_type: Optional[str] = None, limit: int = 100) -> list[Event]:
        if event_type:
            filtered = [e for e in self._event_log if e.type == event_type]
        else:
            filtered = self._event_log
        return filtered[-limit:]

    def clear_log(self) -> None:
        self._event_log.clear()

    @property
    def subscriber_count(self) -> dict[str, int]:
        counts = {}
        for event_type, handlers in self._handlers.items():
            counts[event_type] = len(handlers)
        for event_type, handlers in self._async_handlers.items():
            counts[event_type] = counts.get(event_type, 0) + len(handlers)
        return counts


event_bus = EventBus()
