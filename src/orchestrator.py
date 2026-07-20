from typing import Any
from datetime import datetime
from collections import defaultdict

from .agent import Agent, AgentStatus
from .message import Message, MessageType
from .task import Task, TaskStatus, TaskPriority
from .context import SharedContext


class Orchestrator:
    """The central coordinator for all agents.
    
    The orchestrator is the brain of the platform. It:
    - Registers agents
    - Receives tasks from users
    - Assigns tasks to the right agents
    - Tracks progress
    - Provides status updates
    
    Think of it as a project manager who knows what everyone
    is good at and分配 work accordingly.
    
    Example:
        orch = Orchestrator()
        orch.register_agent(my_agent)
        task = orch.create_task("Analyze data", required_capabilities=["analysis"])
        result = orch.run_task(task)
    """
    
    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self.tasks: dict[str, Task] = {}
        self.message_log: list[Message] = []
        self.context = SharedContext()
        self._task_counter = 0
    
    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the orchestrator."""
        self.agents[agent.id] = agent
        print(f"[Orchestrator] Registered agent: {agent.name} ({agent.id})")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Remove an agent from the orchestrator."""
        if agent_id in self.agents:
            agent = self.agents.pop(agent_id)
            print(f"[Orchestrator] Unregistered agent: {agent.name}")
    
    def create_task(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        required_capabilities: list[str] | None = None,
        input_data: dict | None = None,
    ) -> Task:
        """Create a new task and add it to the queue."""
        self._task_counter += 1
        task = Task(
            name=name,
            description=description,
            priority=priority,
            required_capabilities=required_capabilities or [],
            input_data=input_data or {},
        )
        self.tasks[task.id] = task
        print(f"[Orchestrator] Created task: {task}")
        return task
    
    def find_agent_for_task(self, task: Task) -> Agent | None:
        """Find the best available agent for a task.
        
        Strategy:
        1. Filter agents by capabilities
        2. Filter by availability (not busy)
        3. Pick the one with fewest completed tasks (load balancing)
        """
        suitable_agents = [
            agent for agent in self.agents.values()
            if agent.can_handle(task) and agent.status == AgentStatus.IDLE
        ]
        
        if not suitable_agents:
            return None
        
        # Load balancing: pick agent with fewest completed tasks
        return min(suitable_agents, key=lambda a: len(a.completed_tasks))
    
    def assign_task(self, task: Task, agent: Agent) -> bool:
        """Assign a task to a specific agent.
        
        The task object is passed directly to the agent so that
        results are reflected in the original task.
        """
        if not agent.can_handle(task):
            print(f"[Orchestrator] Agent {agent.name} cannot handle task: {task.name}")
            return False
        
        if agent.status == AgentStatus.BUSY:
            print(f"[Orchestrator] Agent {agent.name} is busy")
            return False
        
        task.status = TaskStatus.ASSIGNED
        task.assigned_to = agent.id
        
        # Process task directly (simpler and keeps task object in sync)
        try:
            agent.current_task = task
            agent.status = AgentStatus.BUSY
            
            result = agent.process_task(task)
            task.complete(result)
            agent.completed_tasks.append(task)
            agent.current_task = None
            agent.status = AgentStatus.IDLE
            
            print(f"[Orchestrator] Task completed by {agent.name}: {task.name}")
            return True
        except Exception as e:
            task.fail(str(e))
            agent.status = AgentStatus.ERROR
            print(f"[Orchestrator] Task failed: {str(e)}")
            return False
    
    def auto_assign_task(self, task: Task) -> bool:
        """Automatically find and assign an agent for a task."""
        agent = self.find_agent_for_task(task)
        if agent:
            return self.assign_task(task, agent)
        
        print(f"[Orchestrator] No suitable agent found for task: {task.name}")
        return False
    
    def create_and_run_task(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        required_capabilities: list[str] | None = None,
        input_data: dict | None = None,
    ) -> dict | None:
        """Create a task and immediately try to run it.
        
        Convenience method that combines create_task + auto_assign_task.
        
        Returns:
            Task results if successful, None if no agent available
        """
        task = self.create_task(
            name=name,
            description=description,
            priority=priority,
            required_capabilities=required_capabilities,
            input_data=input_data,
        )
        
        success = self.auto_assign_task(task)
        
        if success and task.status == TaskStatus.COMPLETED:
            return task.output_data
        return None
    
    def get_status(self) -> dict:
        """Get a summary of the orchestrator's status."""
        agent_stats = defaultdict(int)
        for agent in self.agents.values():
            agent_stats[agent.status.value] += 1
        
        task_stats = defaultdict(int)
        for task in self.tasks.values():
            task_stats[task.status.value] += 1
        
        return {
            "total_agents": len(self.agents),
            "agent_status": dict(agent_stats),
            "total_tasks": len(self.tasks),
            "task_status": dict(task_stats),
            "messages_sent": len(self.message_log),
        }
    
    def print_status(self) -> None:
        """Print a formatted status report."""
        status = self.get_status()
        print("\n" + "="*50)
        print("ORCHESTRATOR STATUS")
        print("="*50)
        print(f"Agents: {status['total_agents']} total")
        for s, count in status['agent_status'].items():
            print(f"  - {s}: {count}")
        print(f"\nTasks: {status['total_tasks']} total")
        for s, count in status['task_status'].items():
            print(f"  - {s}: {count}")
        print(f"\nMessages: {status['messages_sent']}")
        print("="*50 + "\n")
    
    def __repr__(self) -> str:
        return f"Orchestrator(agents={len(self.agents)}, tasks={len(self.tasks)})"
