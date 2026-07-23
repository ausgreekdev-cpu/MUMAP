from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging

from ..deps import get_current_user, get_task_service, get_orchestrator_service
from ...schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from ...services.task_service import TaskService
from ...services.orchestrator import OrchestratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    result = await service.list_tasks(
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        creator_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return result


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    try:
        result = await service.create_task(
            name=task_data.name,
            creator_id=current_user.id,
            description=task_data.description,
            priority=task_data.priority,
            required_capabilities=task_data.required_capabilities,
            input_data=task_data.input_data,
            task_type=task_data.task_type,
            max_retries=task_data.max_retries,
            timeout_seconds=task_data.timeout_seconds,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    result = await service.get_task(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    updates = task_data.model_dump(exclude_unset=True)
    try:
        result = await service.update_task(task_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    try:
        deleted = await service.delete_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return None


@router.post("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: int,
    agent_id: int,
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    try:
        result = await service.assign_task(task_id, agent_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/{task_id}/auto-assign", response_model=TaskResponse)
async def auto_assign_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    result = await service.auto_assign(task_id)
    if not result:
        raise HTTPException(status_code=400, detail="No suitable agent found")
    return result


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    output_data: dict = {},
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    try:
        result = await service.complete_task(task_id, output_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/{task_id}/fail", response_model=TaskResponse)
async def fail_task(
    task_id: int,
    error_message: str = "Task failed",
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    try:
        result = await service.fail_task(task_id, error_message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    try:
        result = await service.cancel_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    try:
        result = await service.retry_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: int,
    limit: int = Query(100, ge=1, le=1000),
    service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    return await service.get_task_logs(task_id, limit=limit)
