from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.agent import Agent
from ..models.marketplace import AgentTemplate, TemplateInstallation
from ..schemas.marketplace import (
    TemplateResponse,
    TemplateListResponse,
    InstallationResponse,
    InstallationListResponse,
    InstallRequest,
    InstallResponse,
)
from ..services.auth import get_current_user
from ..services.websocket import manager

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

CATEGORY_ROLES = {
    "Research": "researcher",
    "Coding": "coder",
    "Writing": "writer",
    "Analysis": "analyzer",
    "Custom": "worker",
}


def _unique_agent_name(db: Session, base: str) -> str:
    if not db.query(Agent).filter(Agent.name == base).first():
        return base
    for i in range(2, 1000):
        candidate = f"{base} {i}"
        if not db.query(Agent).filter(Agent.name == candidate).first():
            return candidate
    raise HTTPException(status_code=400, detail="Too many agents with this name")


@router.get("/templates", response_model=TemplateListResponse)
def list_templates(
    search: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(AgentTemplate).filter(AgentTemplate.is_public.is_(True))

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            AgentTemplate.name.ilike(term) | AgentTemplate.description.ilike(term)
        )
    if category and category != "All":
        query = query.filter(AgentTemplate.category == category)

    total = query.count()
    templates = (
        query.order_by(AgentTemplate.installs_count.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return TemplateListResponse(templates=templates, total=total)


@router.get("/templates/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    template = db.query(AgentTemplate).filter(AgentTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/templates/{template_id}/install", response_model=InstallResponse)
async def install_template(
    template_id: int,
    body: InstallRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    template = db.query(AgentTemplate).filter(AgentTemplate.id == template_id).first()
    if not template or not template.is_public:
        raise HTTPException(status_code=404, detail="Template not found")

    existing = (
        db.query(TemplateInstallation)
        .filter(
            TemplateInstallation.template_id == template_id,
            TemplateInstallation.user_id == current_user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Template already installed")

    agent_name = _unique_agent_name(db, (body.name or template.name).strip())
    agent = Agent(
        owner_id=current_user.id,
        name=agent_name,
        description=template.description,
        role=CATEGORY_ROLES.get(template.category, "worker"),
        capabilities=template.capabilities or [],
        system_prompt=template.system_prompt,
        model_provider=template.model_provider,
        model_name=template.model_name,
        temperature=template.temperature,
        max_tokens=template.max_tokens,
        config=template.config or {},
    )
    db.add(agent)
    db.flush()

    template.installs_count = (template.installs_count or 0) + 1
    installation = TemplateInstallation(
        template_id=template.id,
        user_id=current_user.id,
        agent_id=agent.id,
    )
    db.add(installation)
    db.commit()
    db.refresh(agent)
    db.refresh(installation)
    db.refresh(template)

    try:
        await manager.notify_agent_update({
            "id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "event": "installed_from_marketplace",
        })
    except Exception:
        pass

    return InstallResponse(
        installation=installation,
        template=template,
        agent_id=agent.id,
        agent_name=agent.name,
    )


@router.get("/installed", response_model=InstallationListResponse)
def list_installed(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(TemplateInstallation).filter(
        TemplateInstallation.user_id == current_user.id
    )
    total = query.count()
    installations = query.order_by(TemplateInstallation.installed_at.desc()).all()
    return InstallationListResponse(installations=installations, total=total)
