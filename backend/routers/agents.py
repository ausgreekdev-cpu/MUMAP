from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.agent import Agent, AgentStatus
from ..schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentListResponse, VALID_MODEL_PROVIDERS
from ..services.auth import get_current_user
from ..services.websocket import manager

router = APIRouter(prefix="/agents", tags=["agents"])


def _validate_provider(provider: Optional[str]) -> None:
    if provider is not None and provider not in VALID_MODEL_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model_provider. Must be one of: {', '.join(VALID_MODEL_PROVIDERS)}",
        )


@router.get("/", response_model=AgentListResponse)
def list_agents(
    status: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Agent)
    
    if status:
        query = query.filter(Agent.status == status)
    if role:
        query = query.filter(Agent.role == role)
    
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    
    return AgentListResponse(agents=agents, total=total)


@router.post("/", response_model=AgentResponse)
def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Check if name exists
    if db.query(Agent).filter(Agent.name == agent_data.name).first():
        raise HTTPException(status_code=400, detail="Agent name already exists")
    
    _validate_provider(agent_data.model_provider)
    
    agent = Agent(
        owner_id=current_user.id,
        name=agent_data.name,
        description=agent_data.description,
        role=agent_data.role,
        capabilities=agent_data.capabilities,
        max_concurrent_tasks=agent_data.max_concurrent_tasks,
        model_provider=agent_data.model_provider,
        model_name=agent_data.model_name,
        system_prompt=agent_data.system_prompt,
        temperature=agent_data.temperature,
        max_tokens=agent_data.max_tokens,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    update_data = agent_data.model_dump(exclude_unset=True)
    if "model_provider" in update_data:
        _validate_provider(update_data["model_provider"])
    for key, value in update_data.items():
        setattr(agent, key, value)
    
    db.commit()
    db.refresh(agent)
    
    return agent


@router.delete("/{agent_id}")
def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    
    return {"message": "Agent deleted"}


@router.post("/{agent_id}/status")
async def update_agent_status(
    agent_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if status not in [s.value for s in AgentStatus]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    agent.status = status
    db.commit()
    
    # Notify WebSocket clients
    await manager.notify_agent_update({
        "id": agent.id,
        "name": agent.name,
        "status": agent.status
    })
    
    return {"message": "Status updated"}
