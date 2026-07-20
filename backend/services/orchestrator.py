from datetime import datetime
from sqlalchemy.orm import Session

from ..models.agent import Agent, AgentStatus
from ..models.task import Task, TaskStatus, TaskLog


class OrchestratorService:
    def __init__(self, db: Session):
        self.db = db
    
    def find_agent_for_task(self, task: Task) -> Agent | None:
        """Find the best available agent for a task."""
        suitable_agents = self.db.query(Agent).filter(
            Agent.status == AgentStatus.IDLE,
            Agent.is_active == 1
        ).all()
        
        if not suitable_agents:
            return None
        
        # Filter by capabilities
        capable_agents = []
        for agent in suitable_agents:
            if not task.required_capabilities:
                capable_agents.append(agent)
            elif all(cap in (agent.capabilities or []) for cap in task.required_capabilities):
                capable_agents.append(agent)
        
        if not capable_agents:
            return None
        
        # Load balancing: pick agent with fewest completed tasks
        return min(capable_agents, key=lambda a: a.completed_tasks_count or 0)
    
    def assign_task(self, task_id: int, agent_id: int) -> Task:
        """Assign a task to a specific agent."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not task:
            raise ValueError("Task not found")
        if not agent:
            raise ValueError("Agent not found")
        
        # Check agent can handle task
        if task.required_capabilities:
            if not all(cap in (agent.capabilities or []) for cap in task.required_capabilities):
                raise ValueError(f"Agent {agent.name} lacks required capabilities")
        
        if agent.status != AgentStatus.IDLE:
            raise ValueError(f"Agent {agent.name} is not available")
        
        # Update task
        task.assigned_to = agent.id
        task.status = TaskStatus.ASSIGNED.value
        task.assigned_at = datetime.utcnow()
        
        # Update agent
        agent.status = AgentStatus.BUSY.value
        agent.current_task_id = task.id
        
        # Create log entry
        log = TaskLog(
            task_id=task.id,
            event="assigned",
            message=f"Assigned to agent {agent.name}"
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def auto_assign_task(self, task_id: int) -> Task | None:
        """Automatically find and assign an agent for a task."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        agent = self.find_agent_for_task(task)
        if agent:
            return self.assign_task(task_id, agent.id)
        return None
    
    def complete_task(self, task_id: int, output_data: dict) -> Task:
        """Mark a task as completed."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        
        task.status = TaskStatus.COMPLETED.value
        task.output_data = output_data
        task.completed_at = datetime.utcnow()
        
        # Update agent
        if task.assigned_to:
            agent = self.db.query(Agent).filter(Agent.id == task.assigned_to).first()
            if agent:
                agent.status = AgentStatus.IDLE.value
                agent.current_task_id = None
                agent.completed_tasks_count = (agent.completed_tasks_count or 0) + 1
        
        # Create log entry
        log = TaskLog(
            task_id=task.id,
            event="completed",
            message="Task completed successfully"
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def fail_task(self, task_id: int, error_message: str) -> Task:
        """Mark a task as failed."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        
        task.status = TaskStatus.FAILED.value
        task.error_message = error_message
        task.completed_at = datetime.utcnow()
        
        # Update agent
        if task.assigned_to:
            agent = self.db.query(Agent).filter(Agent.id == task.assigned_to).first()
            if agent:
                agent.status = AgentStatus.ERROR.value
                agent.current_task_id = None
                agent.failed_tasks_count = (agent.failed_tasks_count or 0) + 1
        
        # Create log entry
        log = TaskLog(
            task_id=task.id,
            event="failed",
            message=error_message
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def cancel_task(self, task_id: int) -> Task:
        """Cancel a task."""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        
        task.status = TaskStatus.CANCELLED.value
        
        # Free up agent
        if task.assigned_to:
            agent = self.db.query(Agent).filter(Agent.id == task.assigned_to).first()
            if agent:
                agent.status = AgentStatus.IDLE.value
                agent.current_task_id = None
        
        # Create log entry
        log = TaskLog(
            task_id=task.id,
            event="cancelled",
            message="Task cancelled"
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def get_stats(self) -> dict:
        """Get orchestrator statistics."""
        from sqlalchemy import func
        
        total_agents = self.db.query(Agent).count()
        idle_agents = self.db.query(Agent).filter(Agent.status == AgentStatus.IDLE).count()
        busy_agents = self.db.query(Agent).filter(Agent.status == AgentStatus.BUSY).count()
        
        total_tasks = self.db.query(Task).count()
        pending_tasks = self.db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        completed_tasks = self.db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
        failed_tasks = self.db.query(Task).filter(Task.status == TaskStatus.FAILED).count()
        
        return {
            "agents": {
                "total": total_agents,
                "idle": idle_agents,
                "busy": busy_agents,
            },
            "tasks": {
                "total": total_tasks,
                "pending": pending_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
            }
        }
