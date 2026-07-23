import pytest
from backend.domain.agent import Agent, AgentStatus, AgentRole
from backend.domain.task import Task, TaskStatus, TaskPriority, InvalidStateTransition
from backend.domain.events import Event, EventTypes, EventBus


class TestAgentDomain:
    def test_agent_creation(self):
        agent = Agent(name="TestAgent", owner_id=1)
        assert agent.name == "TestAgent"
        assert agent.status == AgentStatus.IDLE
        assert agent.capabilities == []

    def test_agent_can_handle(self):
        agent = Agent(name="TestAgent", owner_id=1, capabilities=["math", "analysis"])

        assert agent.can_handle(["math"]) is True
        assert agent.can_handle(["math", "analysis"]) is True
        assert agent.can_handle(["unknown"]) is False
        assert agent.can_handle([]) is True

    def test_agent_assign_task(self):
        agent = Agent(name="TestAgent", owner_id=1)
        agent.assign_task(1)
        assert agent.status == AgentStatus.BUSY
        assert agent.current_task_id == 1

    def test_agent_assign_task_when_busy(self):
        agent = Agent(name="TestAgent", owner_id=1)
        agent.assign_task(1)

        with pytest.raises(ValueError):
            agent.assign_task(2)

    def test_agent_complete_task(self):
        agent = Agent(name="TestAgent", owner_id=1)
        agent.assign_task(1)
        agent.complete_task(duration_seconds=10)

        assert agent.status == AgentStatus.IDLE
        assert agent.current_task_id is None
        assert agent.completed_tasks_count == 1
        assert agent.average_task_time == 10.0

    def test_agent_fail_task(self):
        agent = Agent(name="TestAgent", owner_id=1)
        agent.assign_task(1)
        agent.fail_task("Something went wrong")

        assert agent.status == AgentStatus.ERROR
        assert agent.last_error == "Something went wrong"
        assert agent.failed_tasks_count == 1

    def test_agent_success_rate(self):
        agent = Agent(name="TestAgent", owner_id=1)
        agent.completed_tasks_count = 8
        agent.failed_tasks_count = 2
        assert agent.success_rate == 0.8

    def test_agent_success_rate_empty(self):
        agent = Agent(name="TestAgent", owner_id=1)
        assert agent.success_rate == 1.0


class TestTaskDomain:
    def test_task_creation(self):
        task = Task(name="TestTask")
        assert task.name == "TestTask"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL

    def test_task_assign(self):
        task = Task(name="TestTask")
        task.assign(agent_id=1)
        assert task.status == TaskStatus.ASSIGNED
        assert task.assigned_to == 1
        assert task.assigned_at is not None

    def test_task_assign_invalid_state(self):
        task = Task(name="TestTask")
        task.status = TaskStatus.COMPLETED
        with pytest.raises(InvalidStateTransition):
            task.assign(agent_id=1)

    def test_task_start(self):
        task = Task(name="TestTask")
        task.assign(agent_id=1)
        task.start()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None

    def test_task_complete(self):
        task = Task(name="TestTask")
        task.assign(agent_id=1)
        task.start()
        task.complete({"result": "done"})
        assert task.status == TaskStatus.COMPLETED
        assert task.output_data == {"result": "done"}
        assert task.completed_at is not None

    def test_task_fail(self):
        task = Task(name="TestTask")
        task.assign(agent_id=1)
        task.start()
        task.fail("Error occurred")
        assert task.status == TaskStatus.FAILED
        assert task.error_message == "Error occurred"

    def test_task_cancel(self):
        task = Task(name="TestTask")
        task.cancel()
        assert task.status == TaskStatus.CANCELLED

    def test_task_retry(self):
        task = Task(name="TestTask")
        task.max_retries = 3
        task.fail("Error")
        result = task.retry()
        assert result is True
        assert task.status == TaskStatus.RETRYING
        assert task.retry_count == 1

    def test_task_retry_exceeded(self):
        task = Task(name="TestTask")
        task.max_retries = 2
        task.retry_count = 2
        task.fail("Error")
        result = task.retry()
        assert result is False

    def test_task_is_terminal(self):
        task = Task(name="TestTask")
        assert task.is_terminal is False
        task.status = TaskStatus.COMPLETED
        assert task.is_terminal is True
        task.status = TaskStatus.FAILED
        assert task.is_terminal is True


class TestEventBus:
    def test_publish_subscribe(self):
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe("test.event", handler)

        import asyncio
        asyncio.run(bus.publish(Event(type="test.event", data={"key": "value"})))

        assert len(received) == 1
        assert received[0].data == {"key": "value"}

    def test_wildcard_handler(self):
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event.type)

        bus.subscribe("*", handler)

        import asyncio
        asyncio.run(bus.publish(Event(type="any.event", data={})))
        asyncio.run(bus.publish(Event(type="another.event", data={})))

        assert len(received) == 2
        assert "any.event" in received
        assert "another.event" in received

    def test_event_log(self):
        bus = EventBus()

        import asyncio
        asyncio.run(bus.publish(Event(type="test1", data={})))
        asyncio.run(bus.publish(Event(type="test2", data={})))

        log = bus.get_event_log()
        assert len(log) == 2

        log = bus.get_event_log(event_type="test1")
        assert len(log) == 1
