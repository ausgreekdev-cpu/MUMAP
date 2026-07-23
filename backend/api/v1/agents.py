from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging

from ..deps import get_current_user, get_agent_service
from ...schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentListResponse
from ...services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    status: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: AgentService = Depends(get_agent_service),
    current_user=Depends(get_current_user),
):
    result = await service.list_agents(
        status=status,
        role=role,
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return result


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent_data: AgentCreate,
    service: AgentService = Depends(get_agent_service),
    current_user=Depends(get_current_user),
):
    try:
        result = await service.create_agent(
            name=agent_data.name,
            owner_id=current_user.id,
            description=agent_data.description,
            role=agent_data.role,
            capabilities=agent_data.capabilities,
            max_concurrent_tasks=agent_data.max_concurrent_tasks,
            timeout_seconds=agent_data.timeout_seconds,
            organization_id=agent_data.organization_id,
            model_provider=agent_data.model_provider,
            model_name=agent_data.model_name,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    service: AgentService = Depends(get_agent_service),
    current_user=Depends(get_current_user),
):
    result = await service.get_agent(agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    service: AgentService = Depends(get_agent_service),
    current_user=Depends(get_current_user),
):
    updates = agent_data.model_dump(exclude_unset=True)
    result = await service.update_agent(agent_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: int,
    service: AgentService = Depends(get_agent_service),
    current_user=Depends(get_current_user),
):
    deleted = await service.delete_agent(agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None


@router.post("/{agent_id}/status")
async def update_agent_status(
    agent_id: int,
    status: str,
    service: AgentService = Depends(get_agent_service),
    current_user=Depends(get_current_user),
):
    try:
        result = await service.update_status(agent_id, status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Status updated"}


@router.get("/{agent_id}/stats")
async def get_agent_stats(
    agent_id: int,
    service: AgentService = Depends(get_agent_service),
    current_user=Depends(get_current_user),
):
    result = await service.get_agent_stats(agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result


@router.post("/{agent_id}/deactivate")
async def deactivate_agent(
    agent_id: int,
    service: AgentService = Depends(get_agent_service),
    current_user=Depends(get_current_user),
):
    result = await service.deactivate_agent(agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result


@router.post("/{agent_id}/activate")
async def activate_agent(
    agent_id: int,
    service: AgentService = Depends(get_agent_service),
    current_user=Depends(get_current_user),
):
    result = await service.activate_agent(agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result


@router.get("/idle/")
async def get_idle_agents(
    service: AgentService = Depends(get_agent_service),
    current_user=Depends(get_current_user),
):
    return await service.get_idle_agents()


@router.get("/capable/")
async def get_capable_agents(
    capabilities: str = Query("", description="Comma-separated capabilities"),
    service: AgentService = Depends(get_agent_service),
    current_user=Depends(get_current_user),
):
    cap_list = [c.strip() for c in capabilities.split(",") if c.strip()]
    return await service.get_capable_agents(cap_list)
