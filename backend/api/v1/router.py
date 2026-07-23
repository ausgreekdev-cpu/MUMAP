from fastapi import APIRouter
import logging

from .auth import router as auth_router
from .agents import router as agents_router
from .tasks import router as tasks_router
from .websocket import router as ws_router
from .system import router as system_router
from .templates import router as templates_router

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(agents_router)
router.include_router(tasks_router)
router.include_router(system_router)
router.include_router(ws_router)
router.include_router(templates_router)
