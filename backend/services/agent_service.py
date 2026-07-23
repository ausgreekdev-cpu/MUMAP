from typing import Optional, List
import logging

from ..repositories.agent_repo import AgentRepository
from ..domain.agent import AgentStatus, AgentRole
from ..domain.events import Event, EventTypes, event_bus

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, agent_repo: AgentRepository, event_bus_instance=event_bus):
        self.agent_repo = agent_repo
        self.event_bus = event_bus_instance

    async def create_agent(
        self,
        name: str,
        owner_id: int,
        description: str = "",
        role: str = "worker",
        capabilities: List[str] = None,
        max_concurrent_tasks: int = 1,
        timeout_seconds: int = 300,
        organization_id: int = None,
        model_provider: str = None,
        model_name: str = None,
    ) -> dict:
        existing = self.agent_repo.get_by_name(name)
        if existing:
            raise ValueError(f"Agent with name '{name}' already exists")

        agent_data = {
            "name": name,
            "owner_id": owner_id,
            "description": description,
            "role": role,
            "capabilities": capabilities or [],
            "max_concurrent_tasks": max_concurrent_tasks,
            "timeout_seconds": timeout_seconds,
            "organization_id": organization_id,
            "model_provider": model_provider,
            "model_name": model_name,
        }

        agent = self.agent_repo.create(agent_data)

        await self.event_bus.publish(Event(
            type=EventTypes.AGENT_CREATED,
            data=agent.to_dict(),
            source="agent_service",
        ))

        logger.info(f"Agent created: {agent.name} (ID: {agent.id})")
        return agent.to_dict()

    async def get_agent(self, agent_id: int) -> Optional[dict]:
        agent = self.agent_repo.get(agent_id)
        if not agent:
            return None
        return agent.to_dict()

    async def list_agents(
        self,
        status: Optional[str] = None,
        role: Optional[str] = None,
        owner_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        filters = {}
        if status:
            filters["status"] = status
        if role:
            filters["role"] = role
        if owner_id:
            filters["owner_id"] = owner_id
        if organization_id:
            filters["organization_id"] = organization_id

        agents = self.agent_repo.get_multi(skip=skip, limit=limit, filters=filters)
        total = self.agent_repo.count(filters=filters)

        return {
            "agents": [a.to_dict() for a in agents],
            "total": total,
        }

    async def update_agent(self, agent_id: int, updates: dict) -> Optional[dict]:
        agent = self.agent_repo.get(agent_id)
        if not agent:
            return None

        old_data = agent.to_dict()
        updated = self.agent_repo.update(agent_id, updates)

        await self.event_bus.publish(Event(
            type=EventTypes.AGENT_UPDATED,
            data={"old": old_data, "new": updated.to_dict()},
            source="agent_service",
        ))

        logger.info(f"Agent updated: {updated.name} (ID: {updated.id})")
        return updated.to_dict()

    async def delete_agent(self, agent_id: int) -> bool:
        agent = self.agent_repo.get(agent_id)
        if not agent:
            return False

        agent_data = agent.to_dict()
        deleted = self.agent_repo.delete(agent_id)

        if deleted:
            await self.event_bus.publish(Event(
                type=EventTypes.AGENT_DELETED,
                data=agent_data,
                source="agent_service",
            ))
            logger.info(f"Agent deleted: {agent_data['name']} (ID: {agent_id})")

        return deleted

    async def update_status(self, agent_id: int, status: str) -> Optional[dict]:
        valid_statuses = [s.value for s in AgentStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        agent = self.agent_repo.get(agent_id)
        if not agent:
            return None

        old_status = agent.status
        updated = self.agent_repo.update_status(agent_id, status)

        await self.event_bus.publish(Event(
            type=EventTypes.AGENT_STATUS_CHANGED,
            data={
                "agent_id": agent_id,
                "old_status": old_status,
                "new_status": status,
            },
            source="agent_service",
        ))

        return updated.to_dict()

    async def get_idle_agents(self) -> List[dict]:
        agents = self.agent_repo.get_idle_agents()
        return [a.to_dict() for a in agents]

    async def get_capable_agents(self, capabilities: List[str]) -> List[dict]:
        agents = self.agent_repo.get_capable_agents(capabilities)
        return [a.to_dict() for a in agents]

    async def deactivate_agent(self, agent_id: int) -> Optional[dict]:
        agent = self.agent_repo.deactivate(agent_id)
        if not agent:
            return None
        return agent.to_dict()

    async def activate_agent(self, agent_id: int) -> Optional[dict]:
        agent = self.agent_repo.activate(agent_id)
        if not agent:
            return None
        return agent.to_dict()

    async def get_agent_stats(self, agent_id: int) -> Optional[dict]:
        agent = self.agent_repo.get(agent_id)
        if not agent:
            return None
        return {
            "id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "completed_tasks_count": agent.completed_tasks_count or 0,
            "failed_tasks_count": agent.failed_tasks_count or 0,
            "average_task_time": agent.average_task_time or 0,
            "health_score": agent.health_score or 1.0,
            "success_rate": agent.success_rate,
        }
