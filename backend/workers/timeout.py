import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.task import Task, TaskStatus
from ..models.agent import Agent, AgentStatus
from ..domain.events import Event, EventTypes, event_bus

logger = logging.getLogger(__name__)


class TaskTimeoutWorker:
    def __init__(self, check_interval: int = 60, default_timeout: int = 3600):
        self.check_interval = check_interval
        self.default_timeout = default_timeout
        self._running = False

    async def start(self):
        self._running = True
        logger.info(f"Task timeout worker started (interval={self.check_interval}s)")

        while self._running:
            try:
                await self._check_timeouts()
            except Exception as e:
                logger.error(f"Error in timeout worker: {e}")

            await asyncio.sleep(self.check_interval)

    def stop(self):
        self._running = False
        logger.info("Task timeout worker stopped")

    async def _check_timeouts(self):
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(seconds=self.default_timeout)

            timed_out_tasks = db.query(Task).filter(
                Task.status == TaskStatus.IN_PROGRESS.value,
                Task.started_at < cutoff,
            ).all()

            for task in timed_out_tasks:
                await self._handle_timeout(db, task)

            if timed_out_tasks:
                logger.info(f"Processed {len(timed_out_tasks)} timed out tasks")

        finally:
            db.close()

    async def _handle_timeout(self, db: Session, task: Task):
        logger.warning(
            f"Task timed out: {task.name} (ID: {task.id}, "
            f"started: {task.started_at})"
        )

        task.status = TaskStatus.TIMEOUT.value
        task.error_message = f"Task timed out after {self.default_timeout} seconds"
        task.completed_at = datetime.utcnow()

        if task.assigned_to:
            agent = db.query(Agent).filter(Agent.id == task.assigned_to).first()
            if agent:
                agent.status = AgentStatus.IDLE.value
                agent.current_task_id = None
                agent.failed_tasks_count = (agent.failed_tasks_count or 0) + 1

        from ..models.task import TaskLog
        log = TaskLog(
            task_id=task.id,
            agent_id=task.assigned_to,
            event="timeout",
            message=f"Task timed out after {self.default_timeout} seconds",
        )
        db.add(log)

        db.commit()

        await event_bus.publish(Event(
            type=EventTypes.TASK_FAILED,
            data={
                "task_id": task.id,
                "error": "timeout",
                "timeout_seconds": self.default_timeout,
            },
            source="timeout_worker",
        ))


worker = TaskTimeoutWorker()


async def start_timeout_worker():
    await worker.start()


def get_timeout_worker() -> TaskTimeoutWorker:
    return worker
