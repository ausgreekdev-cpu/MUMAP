from typing import Optional, List
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.agent import Agent, AgentStatus


class AgentRepository(BaseRepository[Agent]):
    def __init__(self, db: Session):
        super().__init__(Agent, db)

    def get_by_name(self, name: str) -> Optional[Agent]:
        return self.get_by_field("name", name)

    def get_by_owner(self, owner_id: int, skip: int = 0, limit: int = 100) -> List[Agent]:
        return self.get_multi(skip=skip, limit=limit, filters={"owner_id": owner_id})

    def get_by_organization(self, org_id: int, skip: int = 0, limit: int = 100) -> List[Agent]:
        return self.get_multi(skip=skip, limit=limit, filters={"organization_id": org_id})

    def get_idle_agents(self) -> List[Agent]:
        return self.db.query(Agent).filter(
            Agent.status == AgentStatus.IDLE,
            Agent.is_active == True,
        ).all()

    def get_capable_agents(self, capabilities: List[str]) -> List[Agent]:
        idle_agents = self.get_idle_agents()
        if not capabilities:
            return idle_agents
        return [
            agent for agent in idle_agents
            if agent.capabilities and all(cap in agent.capabilities for cap in capabilities)
        ]

    def get_best_agent_for_task(self, required_capabilities: List[str]) -> Optional[Agent]:
        capable = self.get_capable_agents(required_capabilities)
        if not capable:
            return None
        return min(capable, key=lambda a: a.completed_tasks_count or 0)

    def update_status(self, agent_id: int, status: str) -> Optional[Agent]:
        return self.update(agent_id, {"status": status})

    def increment_completed(self, agent_id: int) -> Optional[Agent]:
        agent = self.get(agent_id)
        if agent:
            agent.completed_tasks_count = (agent.completed_tasks_count or 0) + 1
            self.db.commit()
            self.db.refresh(agent)
        return agent

    def increment_failed(self, agent_id: int) -> Optional[Agent]:
        agent = self.get(agent_id)
        if agent:
            agent.failed_tasks_count = (agent.failed_tasks_count or 0) + 1
            agent.error_count = (agent.error_count or 0) + 1
            self.db.commit()
            self.db.refresh(agent)
        return agent

    def deactivate(self, agent_id: int) -> Optional[Agent]:
        return self.update(agent_id, {"is_active": False, "status": "offline"})

    def activate(self, agent_id: int) -> Optional[Agent]:
        return self.update(agent_id, {"is_active": True, "status": "idle"})
