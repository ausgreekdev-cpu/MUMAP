from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..models.task import Task, TaskStatus, TaskLog
from ..schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse, TaskLogResponse, TaskAssignRequest
from ..services.auth import get_current_user
from ..services.audit import get_audit_logger, request_context
from ..services.orchestrator import OrchestratorService
from ..services.webhook import WebhookEvent, WebhookService
from ..services.websocket import manager

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _schedule_webhook(
    background_tasks: BackgroundTasks, db: Session, event: str, task: Task, **extra
) -> None:
    if not task.creator_id:
        return
    data = {
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "priority": task.priority,
        "creator_id": task.creator_id,
        "assigned_to": task.assigned_to,
    }
    data.update(extra)
    service = WebhookService(db)
    background_tasks.add_task(
        service.trigger_event, event, data, user_id=task.creator_id
    )


@router.get("/", response_model=TaskListResponse)
def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    
    query = query.order_by(Task.created_at.desc())
    total = query.count()
    tasks = query.offset(skip).limit(limit).all()
    
    return TaskListResponse(tasks=tasks, total=total)


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    task = Task(
        name=task_data.name,
        description=task_data.description,
        priority=task_data.priority,
        required_capabilities=task_data.required_capabilities,
        input_data=task_data.input_data,
        creator_id=current_user.id,
    )
    db.add(task)
    db.flush()
    get_audit_logger(db).log(
        action="CREATE",
        resource_type="task",
        resource_id=task.id,
        user_id=current_user.id,
        new_values={"name": task.name, "priority": task.priority},
        **request_context(request),
    )
    db.commit()
    db.refresh(task)
    
    # Notify WebSocket clients
    await manager.notify_task_update({
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "event": "created"
    })
    _schedule_webhook(background_tasks, db, WebhookEvent.TASK_CREATED, task)
    
    return task


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in [TaskStatus.PENDING.value]:
        raise HTTPException(status_code=400, detail="Can only update pending tasks")
    
    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status not in [TaskStatus.PENDING.value, TaskStatus.CANCELLED.value]:
        raise HTTPException(status_code=400, detail="Can only delete pending or cancelled tasks")
    
    old_values = {"name": task.name, "status": task.status}
    db.delete(task)
    get_audit_logger(db).log(
        action="DELETE",
        resource_type="task",
        resource_id=task_id,
        user_id=current_user.id,
        old_values=old_values,
        **request_context(request),
    )
    db.commit()
    
    return {"message": "Task deleted"}


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: int,
    assign_data: TaskAssignRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    orchestrator = OrchestratorService(db)
    
    try:
        task = orchestrator.assign_task(task_id, assign_data.agent_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Notify WebSocket clients
    await manager.notify_task_update({
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "assigned_to": task.assigned_to,
        "event": "assigned"
    })
    _schedule_webhook(background_tasks, db, WebhookEvent.TASK_ASSIGNED, task)
    
    return task


@router.post("/{task_id}/auto-assign", response_model=TaskResponse)
async def auto_assign_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    orchestrator = OrchestratorService(db)
    
    task = orchestrator.auto_assign_task(task_id)
    if not task:
        raise HTTPException(status_code=400, detail="No suitable agent found")
    
    # Notify WebSocket clients
    await manager.notify_task_update({
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "assigned_to": task.assigned_to,
        "event": "assigned"
    })
    _schedule_webhook(background_tasks, db, WebhookEvent.TASK_ASSIGNED, task)
    
    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    output_data: dict = {},
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    orchestrator = OrchestratorService(db)
    
    try:
        task = orchestrator.complete_task(task_id, output_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Notify WebSocket clients
    await manager.notify_task_update({
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "event": "completed"
    })
    _schedule_webhook(background_tasks, db, WebhookEvent.TASK_COMPLETED, task)
    
    return task


@router.post("/{task_id}/fail", response_model=TaskResponse)
async def fail_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    error_message: str = "Task failed",
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    orchestrator = OrchestratorService(db)
    
    try:
        task = orchestrator.fail_task(task_id, error_message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Notify WebSocket clients
    await manager.notify_task_update({
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "event": "failed"
    })
    _schedule_webhook(
        background_tasks, db, WebhookEvent.TASK_FAILED, task, error=error_message
    )
    
    return task


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    orchestrator = OrchestratorService(db)
    
    try:
        task = orchestrator.cancel_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Notify WebSocket clients
    await manager.notify_task_update({
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "event": "cancelled"
    })
    _schedule_webhook(background_tasks, db, WebhookEvent.TASK_CANCELLED, task)
    
    return task


@router.get("/{task_id}/logs", response_model=list[TaskLogResponse])
def get_task_logs(
    task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    logs = db.query(TaskLog).filter(TaskLog.task_id == task_id).order_by(TaskLog.created_at.asc()).all()
    return logs
