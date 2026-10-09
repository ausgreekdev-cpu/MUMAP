import json
from typing import Optional, Any
from datetime import datetime
from fastapi import Request
from sqlalchemy.orm import Session

from ..models.user import AuditLog


def request_context(request: Request) -> dict:
    """Extract endpoint/method/ip/user-agent for AuditLogger.log kwargs."""
    return {
        "endpoint": request.url.path,
        "method": request.method,
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


class AuditLogger:
    """Audit logging service for tracking all actions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        user_id: Optional[int] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            old_values=old_values,
            new_values=new_values,
            success=success,
            error_message=error_message,
        )
        
        self.db.add(log_entry)
        self.db.flush()  # Get the ID without committing
        
        return log_entry
    
    def log_create(
        self,
        resource_type: str,
        resource_id: int,
        new_values: dict,
        user_id: Optional[int] = None,
        **kwargs
    ) -> AuditLog:
        """Log a create action."""
        return self.log(
            action="CREATE",
            resource_type=resource_type,
            resource_id=resource_id,
            new_values=new_values,
            user_id=user_id,
            **kwargs
        )
    
    def log_update(
        self,
        resource_type: str,
        resource_id: int,
        old_values: dict,
        new_values: dict,
        user_id: Optional[int] = None,
        **kwargs
    ) -> AuditLog:
        """Log an update action."""
        return self.log(
            action="UPDATE",
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            **kwargs
        )
    
    def log_delete(
        self,
        resource_type: str,
        resource_id: int,
        old_values: dict,
        user_id: Optional[int] = None,
        **kwargs
    ) -> AuditLog:
        """Log a delete action."""
        return self.log(
            action="DELETE",
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            user_id=user_id,
            **kwargs
        )
    
    def log_login(
        self,
        user_id: int,
        success: bool = True,
        error_message: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """Log a login attempt."""
        return self.log(
            action="LOGIN",
            resource_type="user",
            resource_id=user_id,
            user_id=user_id,
            success=success,
            error_message=error_message,
            **kwargs
        )
    
    def get_logs(
        self,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Query audit logs with filters."""
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        if action:
            query = query.filter(AuditLog.action == action)
        
        return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()


def get_audit_logger(db: Session) -> AuditLogger:
    """Factory function for audit logger."""
    return AuditLogger(db)
