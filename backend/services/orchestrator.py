from typing import Optional, List
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from ..repositories.agent_repo import AgentRepository
from ..repositories.task_repo import TaskRepository
from ..domain.events import Event, EventTypes, event_bus

logger = logging.getLogger(__name__)


class OrchestratorService:
    def __init__(self, db: Session, event_bus_instance=event_bus):
        self.agent_repo = AgentRepository(db)
        self.task_repo = TaskRepository(db)
        self.event_bus = event_bus_instance

    async def find_best_agent(self, task_id: int) -> Optional[dict]:
        task = self.task_repo.get(task_id)
        if not task:
            return None

        agent = self.agent_repo.get_best_agent_for_task(
            task.required_capabilities or []
        )

        if not agent:
            return None

        return agent.to_dict()

    async def auto_assign_and_start(self, task_id: int) -> Optional[dict]:
        task = self.task_repo.get(task_id)
        if not task:
            return None

        agent = self.agent_repo.get_best_agent_for_task(
            task.required_capabilities or []
        )

        if not agent:
            logger.warning(f"No suitable agent found for task {task_id}")
            return None

        task = self.task_repo.assign(task_id, agent.id)
        agent.assign_task(task_id)
        self.agent_repo.db.commit()

        self.task_repo.add_log(
            task_id,
            "assigned",
            f"Auto-assigned to agent {agent.name}",
            agent_id=agent.id,
        )

        await self.event_bus.publish(Event(
            type=EventTypes.TASK_ASSIGNED,
            data={
                "task_id": task_id,
                "agent_id": agent.id,
                "agent_name": agent.name,
                "auto_assigned": True,
            },
            source="orchestrator",
        ))

        logger.info(f"Task {task_id} auto-assigned to agent {agent.name}")
        return task.to_dict()

    async def get_system_status(self) -> dict:
        total_agents = self.agent_repo.count()
        idle_agents = len(self.agent_repo.get_idle_agents())
        busy_agents = self.agent_repo.count({"status": "busy"})

        total_tasks = self.task_repo.count()
        pending_tasks = self.task_repo.count({"status": "pending"})
        in_progress_tasks = self.task_repo.count({"status": "in_progress"})
        completed_tasks = self.task_repo.count({"status": "completed"})
        failed_tasks = self.task_repo.count({"status": "failed"})

        return {
            "agents": {
                "total": total_agents,
                "idle": idle_agents,
                "busy": busy_agents,
                "error": self.agent_repo.count({"status": "error"}),
            },
            "tasks": {
                "total": total_tasks,
                "pending": pending_tasks,
                "in_progress": in_progress_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
            },
            "system": {
                "uptime": self._get_uptime(),
                "event_subscribers": self.event_bus.subscriber_count,
            },
        }

    async def get_agent_for_task(self, task_id: int) -> Optional[dict]:
        return await self.find_best_agent(task_id)

    async def rebalance_agents(self) -> List[dict]:
        stuck_tasks = self.task_repo.get_stale_tasks(timeout_minutes=30)
        results = []

        for task in stuck_tasks:
            if task.assigned_to:
                agent = self.agent_repo.get(task.assigned_to)
                if agent:
                    agent.status = "idle"
                    agent.current_task_id = None

            task.status = "pending"
            task.assigned_to = None
            task.assigned_at = None
            results.append(task.to_dict())

        self.agent_repo.db.commit()

        if results:
            logger.warning(f"Rebalanced {len(results)} stuck tasks")
            await self.event_bus.publish(Event(
                type=EventTypes.SYSTEM_ERROR,
                data={"action": "rebalance", "tasks_affected": len(results)},
                source="orchestrator",
            ))

        return results

    def _get_uptime(self) -> float:
        import time
        if not hasattr(self, '_start_time'):
            self._start_time = time.time()
        return time.time() - self._start_time
