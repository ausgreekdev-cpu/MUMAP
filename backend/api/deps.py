from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import logging

from ..config import settings
from ..database import get_db
from ..repositories.agent_repo import AgentRepository
from ..repositories.task_repo import TaskRepository, TaskLogRepository
from ..repositories.user_repo import UserRepository
from ..services.agent_service import AgentService
from ..services.task_service import TaskService
from ..services.orchestrator import OrchestratorService
from ..domain.events import event_bus

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_repo = UserRepository(db)
        user = user_repo.get(int(user_id))
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is disabled")

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


async def require_admin(current_user=Depends(get_current_user)):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def get_agent_repo(db: Session = Depends(get_db)) -> AgentRepository:
    return AgentRepository(db)


def get_task_repo(db: Session = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)


def get_task_log_repo(db: Session = Depends(get_db)) -> TaskLogRepository:
    return TaskLogRepository(db)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_agent_service(
    agent_repo: AgentRepository = Depends(get_agent_repo),
) -> AgentService:
    return AgentService(agent_repo, event_bus)


def get_task_service(
    task_repo: TaskRepository = Depends(get_task_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
    task_log_repo: TaskLogRepository = Depends(get_task_log_repo),
) -> TaskService:
    return TaskService(task_repo, agent_repo, task_log_repo, event_bus)


def get_orchestrator_service(
    db: Session = Depends(get_db),
) -> OrchestratorService:
    return OrchestratorService(db, event_bus)
