"""Tests for the multi-agent platform."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import Agent, Orchestrator, Task, TaskPriority, TaskStatus, SharedContext
from src.agent import AgentConfig, AgentStatus
from src.message import Message, MessageType


class SimpleAgent(Agent):
    """A simple test agent."""
    
    def __init__(self, name: str = "TestBot", capabilities: list[str] | None = None):
        config = AgentConfig(
            name=name,
            capabilities=capabilities or ["test"],
        )
        super().__init__(config)
    
    def process_task(self, task: Task) -> dict:
        return {"processed": True, "task_name": task.name}


class FailingAgent(Agent):
    """An agent that always fails."""
    
    def __init__(self):
        config = AgentConfig(name="FailBot", capabilities=["fail"])
        super().__init__(config)
    
    def process_task(self, task: Task) -> dict:
        raise ValueError("Intentional failure")


# ============================================================
# Tests
# ============================================================

def test_agent_creation():
    """Test creating an agent."""
    agent = SimpleAgent("TestBot")
    assert agent.name == "TestBot"
    assert agent.status == AgentStatus.IDLE
    assert "test" in agent.capabilities


def test_agent_can_handle_task():
    """Test agent capability matching."""
    agent = SimpleAgent("TestBot", capabilities=["math", "analysis"])
    
    # Task requiring math - should handle
    task1 = Task(name="Math task", required_capabilities=["math"])
    assert agent.can_handle(task1) is True
    
    # Task requiring unknown capability - should not handle
    task2 = Task(name="Unknown task", required_capabilities=["unknown"])
    assert agent.can_handle(task2) is False
    
    # Task with no requirements - should handle
    task3 = Task(name="Any task")
    assert agent.can_handle(task3) is True


def test_agent_process_task():
    """Test agent processing a task."""
    agent = SimpleAgent()
    task = Task(name="Test task")
    
    result = agent.process_task(task)
    
    assert result["processed"] is True
    assert result["task_name"] == "Test task"
    assert agent.status == AgentStatus.IDLE


def test_orchestrator_register_agent():
    """Test registering agents with orchestrator."""
    orch = Orchestrator()
    agent = SimpleAgent("Bot1")
    
    orch.register_agent(agent)
    
    assert agent.id in orch.agents
    assert orch.agents[agent.id].name == "Bot1"


def test_orchestrator_create_task():
    """Test creating tasks."""
    orch = Orchestrator()
    
    task = orch.create_task("Test task", priority=TaskPriority.HIGH)
    
    assert task.id in orch.tasks
    assert task.name == "Test task"
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.PENDING


def test_orchestrator_auto_assign():
    """Test automatic task assignment."""
    orch = Orchestrator()
    agent = SimpleAgent("Worker", capabilities=["math"])
    
    orch.register_agent(agent)
    
    result = orch.create_and_run_task(
        name="Math task",
        required_capabilities=["math"],
    )
    
    assert result is not None
    assert result["processed"] is True


def test_orchestrator_no_suitable_agent():
    """Test when no agent can handle a task."""
    orch = Orchestrator()
    agent = SimpleAgent("Worker", capabilities=["math"])
    
    orch.register_agent(agent)
    
    result = orch.create_and_run_task(
        name="Unknown task",
        required_capabilities=["unknown_cap"],
    )
    
    assert result is None


def test_orchestrator_multiple_agents():
    """Test load balancing across agents."""
    orch = Orchestrator()
    
    agent1 = SimpleAgent("Worker1", capabilities=["math"])
    agent2 = SimpleAgent("Worker2", capabilities=["math"])
    
    orch.register_agent(agent1)
    orch.register_agent(agent2)
    
    # Run multiple tasks
    for i in range(3):
        result = orch.create_and_run_task(
            name=f"Task {i}",
            required_capabilities=["math"],
        )
        assert result is not None
    
    # Both agents should have some tasks
    assert len(agent1.completed_tasks) + len(agent2.completed_tasks) == 3


def test_orchestrator_status():
    """Test getting orchestrator status."""
    orch = Orchestrator()
    agent = SimpleAgent("Bot1")
    orch.register_agent(agent)
    
    status = orch.get_status()
    
    assert status["total_agents"] == 1
    assert status["total_tasks"] == 0


def test_shared_context():
    """Test shared context operations."""
    ctx = SharedContext()
    
    # Set and get
    ctx.set("key1", "value1", author="test")
    assert ctx.get("key1") == "value1"
    
    # Default value
    assert ctx.get("nonexistent", "default") == "default"
    
    # Delete
    ctx.delete("key1")
    assert ctx.get("key1") is None
    
    # List keys
    ctx.set("a", 1, author="test")
    ctx.set("b", 2)
    assert len(ctx.list_keys()) == 2
    
    # Metadata
    metadata = ctx.get_metadata("a")
    assert metadata["author"] == "test"
    
    # Clear
    ctx.clear()
    assert len(ctx) == 0


def test_task_lifecycle():
    """Test task status transitions."""
    task = Task(name="Lifecycle test")
    
    assert task.status == TaskStatus.PENDING
    
    task.status = TaskStatus.ASSIGNED
    assert task.status == TaskStatus.ASSIGNED
    
    task.complete({"result": "done"})
    assert task.status == TaskStatus.COMPLETED
    assert task.output_data == {"result": "done"}
    assert task.completed_at is not None


def test_failing_agent():
    """Test agent that fails."""
    orch = Orchestrator()
    agent = FailingAgent()
    orch.register_agent(agent)
    
    result = orch.create_and_run_task(
        name="Failing task",
        required_capabilities=["fail"],
    )
    
    assert result is None
    assert agent.status == AgentStatus.ERROR


if __name__ == "__main__":
    # Run all tests
    test_functions = [
        test_agent_creation,
        test_agent_can_handle_task,
        test_agent_process_task,
        test_orchestrator_register_agent,
        test_orchestrator_create_task,
        test_orchestrator_auto_assign,
        test_orchestrator_no_suitable_agent,
        test_orchestrator_multiple_agents,
        test_orchestrator_status,
        test_shared_context,
        test_task_lifecycle,
        test_failing_agent,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"  ✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {test_func.__name__}: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
