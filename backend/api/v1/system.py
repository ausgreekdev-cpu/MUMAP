from fastapi import APIRouter, Depends
import logging

from ..deps import get_current_user, get_orchestrator_service
from ...services.orchestrator import OrchestratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
async def get_system_status(
    service: OrchestratorService = Depends(get_orchestrator_service),
    current_user=Depends(get_current_user),
):
    return await service.get_system_status()


@router.post("/rebalance")
async def rebalance_agents(
    service: OrchestratorService = Depends(get_orchestrator_service),
    current_user=Depends(get_current_user),
):
    rebalanced = await service.rebalance_agents()
    return {
        "message": f"Rebalanced {len(rebalanced)} tasks",
        "tasks": rebalanced,
    }
