from fastapi import APIRouter, Depends, HTTPException
import logging

from ..deps import get_current_user, get_agent_service, get_task_service
from ...services.templates import get_templates, get_template
from ...services.agent_service import AgentService
from ...services.task_service import TaskService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/")
async def list_templates(current_user=Depends(get_current_user)):
    return {"templates": get_templates()}


@router.get("/{template_id}")
async def get_template_detail(template_id: str, current_user=Depends(get_current_user)):
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/{template_id}/deploy")
async def deploy_template(
    template_id: str,
    agent_service: AgentService = Depends(get_agent_service),
    task_service: TaskService = Depends(get_task_service),
    current_user=Depends(get_current_user),
):
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    created_agents = []
    for agent_data in template["agents"]:
        try:
            agent = await agent_service.create_agent(
                name=agent_data["name"],
                owner_id=current_user.id,
                description=agent_data.get("description", ""),
                role=agent_data.get("role", "worker"),
                capabilities=agent_data.get("capabilities", []),
            )
            created_agents.append(agent)
        except ValueError:
            pass

    created_tasks = []
    for task_data in template["tasks"]:
        try:
            task = await task_service.create_task(
                name=task_data["name"],
                creator_id=current_user.id,
                description=task_data.get("description", ""),
                priority=task_data.get("priority", "normal"),
                required_capabilities=task_data.get("required_capabilities", []),
            )
            created_tasks.append(task)
        except Exception:
            pass

    logger.info(f"Template '{template_id}' deployed by user {current_user.id}: {len(created_agents)} agents, {len(created_tasks)} tasks")

    return {
        "message": f"Template '{template['industry']}' deployed successfully",
        "agents_created": len(created_agents),
        "tasks_created": len(created_tasks),
    }
