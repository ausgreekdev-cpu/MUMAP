from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import AuditLog, User
from ..schemas.audit import AuditLogList, AuditLogResponse
from ..services.auth import get_current_user
from ..services.audit import get_audit_logger

router = APIRouter(prefix="/audit", tags=["audit"])


def _base_filters(
    user_id: int,
    action: Optional[str],
    resource_type: Optional[str],
) -> list:
    filters = [AuditLog.user_id == user_id]
    if action:
        filters.append(AuditLog.action == action)
    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)
    return filters


@router.get("/logs", response_model=AuditLogList)
def list_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs = get_audit_logger(db).get_logs(
        user_id=current_user.id,
        action=action,
        resource_type=resource_type,
        limit=limit,
        offset=skip,
    )
    filters = _base_filters(current_user.id, action, resource_type)
    total = db.query(AuditLog).filter(*filters).count()
    return AuditLogList(
        items=[AuditLogResponse.model_validate(entry) for entry in logs],
        total=total,
    )
