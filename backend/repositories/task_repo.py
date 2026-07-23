from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .base import BaseRepository
from ..models.task import Task, TaskStatus, TaskLog, TaskDependency


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: Session):
        super().__init__(Task, db)

    def get_pending_tasks(self, skip: int = 0, limit: int = 100) -> List[Task]:
        return self.get_multi(
            skip=skip,
            limit=limit,
            filters={"status": TaskStatus.PENDING.value},
            order_by="created_at",
        )

    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Task]:
        return self.get_multi(skip=skip, limit=limit, filters={"status": status})

    def get_by_creator(self, creator_id: int, skip: int = 0, limit: int = 100) -> List[Task]:
        return self.get_multi(skip=skip, limit=limit, filters={"creator_id": creator_id})

    def get_by_agent(self, agent_id: int, skip: int = 0, limit: int = 100) -> List[Task]:
        return self.get_multi(skip=skip, limit=limit, filters={"assigned_to": agent_id})

    def get_by_organization(self, org_id: int, skip: int = 0, limit: int = 100) -> List[Task]:
        return self.get_multi(skip=skip, limit=limit, filters={"organization_id": org_id})

    def get_active_tasks(self) -> List[Task]:
        return self.db.query(Task).filter(
            Task.status.in_([
                TaskStatus.PENDING.value,
                TaskStatus.ASSIGNED.value,
                TaskStatus.IN_PROGRESS.value,
            ])
        ).all()

    def get_stale_tasks(self, timeout_minutes: int = 60) -> List[Task]:
        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        return self.db.query(Task).filter(
            Task.status == TaskStatus.IN_PROGRESS.value,
            Task.started_at < cutoff,
        ).all()

    def assign(self, task_id: int, agent_id: int) -> Optional[Task]:
        return self.update(task_id, {
            "status": TaskStatus.ASSIGNED.value,
            "assigned_to": agent_id,
            "assigned_at": datetime.utcnow(),
        })

    def start(self, task_id: int) -> Optional[Task]:
        return self.update(task_id, {
            "status": TaskStatus.IN_PROGRESS.value,
            "started_at": datetime.utcnow(),
        })

    def complete(self, task_id: int, output_data: dict) -> Optional[Task]:
        return self.update(task_id, {
            "status": TaskStatus.COMPLETED.value,
            "output_data": output_data,
            "completed_at": datetime.utcnow(),
        })

    def fail(self, task_id: int, error_message: str) -> Optional[Task]:
        return self.update(task_id, {
            "status": TaskStatus.FAILED.value,
            "error_message": error_message,
            "completed_at": datetime.utcnow(),
        })

    def cancel(self, task_id: int) -> Optional[Task]:
        return self.update(task_id, {"status": TaskStatus.CANCELLED.value})

    def add_log(self, task_id: int, event: str, message: str, agent_id: int = None, data: dict = None) -> TaskLog:
        log = TaskLog(
            task_id=task_id,
            agent_id=agent_id,
            event=event,
            message=message,
            data=data or {},
        )
        self.db.add(log)
        self.db.commit()
        return log

    def get_logs(self, task_id: int, limit: int = 100) -> List[TaskLog]:
        return self.db.query(TaskLog).filter(
            TaskLog.task_id == task_id
        ).order_by(TaskLog.created_at.desc()).limit(limit).all()


class TaskLogRepository(BaseRepository[TaskLog]):
    def __init__(self, db: Session):
        super().__init__(TaskLog, db)

    def get_by_task(self, task_id: int, limit: int = 100) -> List[TaskLog]:
        return self.db.query(TaskLog).filter(
            TaskLog.task_id == task_id
        ).order_by(TaskLog.created_at.desc()).limit(limit).all()

    def get_by_agent(self, agent_id: int, limit: int = 100) -> List[TaskLog]:
        return self.db.query(TaskLog).filter(
            TaskLog.agent_id == agent_id
        ).order_by(TaskLog.created_at.desc()).limit(limit).all()


class TaskDependencyRepository(BaseRepository[TaskDependency]):
    def __init__(self, db: Session):
        super().__init__(TaskDependency, db)

    def get_dependencies(self, task_id: int) -> List[TaskDependency]:
        return self.db.query(TaskDependency).filter(
            TaskDependency.task_id == task_id
        ).all()

    def get_dependents(self, task_id: int) -> List[TaskDependency]:
        return self.db.query(TaskDependency).filter(
            TaskDependency.depends_on_task_id == task_id
        ).all()
