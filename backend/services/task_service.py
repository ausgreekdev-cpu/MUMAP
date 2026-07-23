from typing import Optional, List
from datetime import datetime
import logging

from ..repositories.task_repo import TaskRepository, TaskLogRepository
from ..repositories.agent_repo import AgentRepository
from ..domain.task import TaskStatus, TaskPriority
from ..domain.events import Event, EventTypes, event_bus

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(
        self,
        task_repo: TaskRepository,
        agent_repo: AgentRepository,
        task_log_repo: TaskLogRepository = None,
        event_bus_instance=event_bus,
    ):
        self.task_repo = task_repo
        self.agent_repo = agent_repo
        self.task_log_repo = task_log_repo or TaskLogRepository(task_repo.db)
        self.event_bus = event_bus_instance

    async def create_task(
        self,
        name: str,
        creator_id: int = None,
        organization_id: int = None,
        description: str = "",
        priority: str = "normal",
        required_capabilities: List[str] = None,
        input_data: dict = None,
        task_type: str = "simple",
        max_retries: int = 3,
        timeout_seconds: int = 3600,
    ) -> dict:
        task_data = {
            "name": name,
            "creator_id": creator_id,
            "organization_id": organization_id,
            "description": description,
            "priority": priority,
            "required_capabilities": required_capabilities or [],
            "input_data": input_data or {},
            "task_type": task_type,
            "max_retries": max_retries,
            "timeout_seconds": timeout_seconds,
        }

        task = self.task_repo.create(task_data)

        self.task_log_repo.create({
            "task_id": task.id,
            "event": "created",
            "message": f"Task '{name}' created",
        })

        await self.event_bus.publish(Event(
            type=EventTypes.TASK_CREATED,
            data=task.to_dict(),
            source="task_service",
        ))

        logger.info(f"Task created: {name} (ID: {task.id})")
        return task.to_dict()

    async def get_task(self, task_id: int) -> Optional[dict]:
        task = self.task_repo.get(task_id)
        if not task:
            return None
        return task.to_dict()

    async def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[int] = None,
        creator_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        filters = {}
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        if assigned_to:
            filters["assigned_to"] = assigned_to
        if creator_id:
            filters["creator_id"] = creator_id
        if organization_id:
            filters["organization_id"] = organization_id

        tasks = self.task_repo.get_multi(skip=skip, limit=limit, filters=filters)
        total = self.task_repo.count(filters=filters)

        return {
            "tasks": [t.to_dict() for t in tasks],
            "total": total,
        }

    async def update_task(self, task_id: int, updates: dict) -> Optional[dict]:
        task = self.task_repo.get(task_id)
        if not task:
            return None

        if task.status != TaskStatus.PENDING.value:
            raise ValueError("Can only update pending tasks")

        updated = self.task_repo.update(task_id, updates)
        return updated.to_dict()

    async def delete_task(self, task_id: int) -> bool:
        task = self.task_repo.get(task_id)
        if not task:
            return False

        if task.status not in [TaskStatus.PENDING.value, TaskStatus.CANCELLED.value]:
            raise ValueError("Can only delete pending or cancelled tasks")

        return self.task_repo.delete(task_id)

    async def assign_task(self, task_id: int, agent_id: int) -> dict:
        task = self.task_repo.get(task_id)
        if not task:
            raise ValueError("Task not found")

        agent = self.agent_repo.get(agent_id)
        if not agent:
            raise ValueError("Agent not found")

        if task.required_capabilities:
            if not agent.capabilities:
                raise ValueError(f"Agent {agent.name} has no capabilities")
            if not all(cap in agent.capabilities for cap in task.required_capabilities):
                raise ValueError(f"Agent {agent.name} lacks required capabilities")

        if agent.status != "idle":
            raise ValueError(f"Agent {agent.name} is not available (status: {agent.status})")

        task = self.task_repo.assign(task_id, agent_id)
        self.agent_repo.db.commit()

        self.task_log_repo.create({
            "task_id": task_id,
            "agent_id": agent_id,
            "event": "assigned",
            "message": f"Assigned to agent {agent.name}",
        })

        await self.event_bus.publish(Event(
            type=EventTypes.TASK_ASSIGNED,
            data={"task_id": task_id, "agent_id": agent_id, "agent_name": agent.name},
            source="task_service",
        ))

        logger.info(f"Task {task_id} assigned to agent {agent.name}")
        return task.to_dict()

    async def auto_assign(self, task_id: int) -> Optional[dict]:
        task = self.task_repo.get(task_id)
        if not task:
            return None

        agent = self.agent_repo.get_best_agent_for_task(
            task.required_capabilities or []
        )

        if not agent:
            logger.warning(f"No suitable agent found for task {task_id}")
            return None

        return await self.assign_task(task_id, agent.id)

    async def start_task(self, task_id: int) -> Optional[dict]:
        task = self.task_repo.start(task_id)
        if not task:
            return None

        self.task_log_repo.create({
            "task_id": task_id,
            "agent_id": task.assigned_to,
            "event": "started",
            "message": "Task execution started",
        })

        await self.event_bus.publish(Event(
            type=EventTypes.TASK_STARTED,
            data={"task_id": task_id},
            source="task_service",
        ))

        return task.to_dict()

    async def complete_task(self, task_id: int, output_data: dict) -> dict:
        task = self.task_repo.get(task_id)
        if not task:
            raise ValueError("Task not found")

        completed = self.task_repo.complete(task_id, output_data)

        if task.assigned_to:
            agent = self.agent_repo.get(task.assigned_to)
            if agent:
                duration = 0
                if task.started_at:
                    duration = int((datetime.utcnow() - task.started_at).total_seconds())
                self.agent_repo.increment_completed(task.assigned_to)

        self.task_log_repo.create({
            "task_id": task_id,
            "agent_id": task.assigned_to,
            "event": "completed",
            "message": "Task completed successfully",
        })

        await self.event_bus.publish(Event(
            type=EventTypes.TASK_COMPLETED,
            data={"task_id": task_id, "output_data": output_data},
            source="task_service",
        ))

        logger.info(f"Task {task_id} completed")
        return completed.to_dict()

    async def fail_task(self, task_id: int, error_message: str) -> dict:
        task = self.task_repo.get(task_id)
        if not task:
            raise ValueError("Task not found")

        failed = self.task_repo.fail(task_id, error_message)

        if task.assigned_to:
            self.agent_repo.increment_failed(task.assigned_to)
            agent = self.agent_repo.get(task.assigned_to)
            if agent:
                agent.status = "error"
                agent.current_task_id = None
                agent.last_error = error_message
                self.agent_repo.db.commit()

        self.task_log_repo.create({
            "task_id": task_id,
            "agent_id": task.assigned_to,
            "event": "failed",
            "message": error_message,
        })

        await self.event_bus.publish(Event(
            type=EventTypes.TASK_FAILED,
            data={"task_id": task_id, "error": error_message},
            source="task_service",
        ))

        logger.warning(f"Task {task_id} failed: {error_message}")
        return failed.to_dict()

    async def cancel_task(self, task_id: int) -> dict:
        task = self.task_repo.get(task_id)
        if not task:
            raise ValueError("Task not found")

        cancelled = self.task_repo.cancel(task_id)

        if task.assigned_to:
            agent = self.agent_repo.get(task.assigned_to)
            if agent:
                agent.status = "idle"
                agent.current_task_id = None
                self.agent_repo.db.commit()

        self.task_log_repo.create({
            "task_id": task_id,
            "agent_id": task.assigned_to,
            "event": "cancelled",
            "message": "Task cancelled",
        })

        await self.event_bus.publish(Event(
            type=EventTypes.TASK_CANCELLED,
            data={"task_id": task_id},
            source="task_service",
        ))

        logger.info(f"Task {task_id} cancelled")
        return cancelled.to_dict()

    async def retry_task(self, task_id: int) -> Optional[dict]:
        task = self.task_repo.get(task_id)
        if not task:
            return None

        if task.retry_count >= task.max_retries:
            raise ValueError("Task has exceeded maximum retries")

        updated = self.task_repo.update(task_id, {
            "status": TaskStatus.PENDING.value,
            "retry_count": task.retry_count + 1,
            "error_message": None,
            "assigned_to": None,
            "assigned_at": None,
        })

        self.task_log_repo.create({
            "task_id": task_id,
            "event": "retrying",
            "message": f"Task retrying (attempt {updated.retry_count + 1}/{updated.max_retries})",
        })

        await self.event_bus.publish(Event(
            type=EventTypes.TASK_RETRYING,
            data={"task_id": task_id, "retry_count": updated.retry_count},
            source="task_service",
        ))

        return updated.to_dict()

    async def get_task_logs(self, task_id: int, limit: int = 100) -> List[dict]:
        logs = self.task_log_repo.get_by_task(task_id, limit=limit)
        return [
            {
                "id": log.id,
                "task_id": log.task_id,
                "agent_id": log.agent_id,
                "event": log.event,
                "message": log.message,
                "data": log.data,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    async def get_stats(self, organization_id: int = None) -> dict:
        from sqlalchemy import func

        filters = {}
        if organization_id:
            filters["organization_id"] = organization_id

        total = self.task_repo.count(filters)
        pending = self.task_repo.count({**filters, "status": "pending"})
        in_progress = self.task_repo.count({**filters, "status": "in_progress"})
        completed = self.task_repo.count({**filters, "status": "completed"})
        failed = self.task_repo.count({**filters, "status": "failed"})

        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total if total > 0 else 0,
        }
