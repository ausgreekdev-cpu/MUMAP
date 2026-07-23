from typing import Optional, List
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.user import User, APIKey, AuditLog, Webhook


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.get_by_field("email", email)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.get_by_field("username", username)

    def get_by_api_key(self, api_key: str) -> Optional[User]:
        return self.db.query(User).filter(
            User.api_key == api_key,
            User.api_key_enabled == True,
        ).first()

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.get_multi(skip=skip, limit=limit, filters={"is_active": True})

    def get_admin_users(self) -> List[User]:
        return self.db.query(User).filter(
            User.role.in_(["admin", "super_admin"]),
            User.is_active == True,
        ).all()

    def deactivate(self, user_id: int) -> Optional[User]:
        return self.update(user_id, {"is_active": False})

    def activate(self, user_id: int) -> Optional[User]:
        return self.update(user_id, {"is_active": True})

    def set_api_key(self, user_id: int, api_key: str) -> Optional[User]:
        return self.update(user_id, {
            "api_key": api_key,
            "api_key_enabled": True,
        })

    def revoke_api_key(self, user_id: int) -> Optional[User]:
        return self.update(user_id, {
            "api_key": None,
            "api_key_enabled": False,
        })


class APIKeyRepository(BaseRepository[APIKey]):
    def __init__(self, db: Session):
        super().__init__(APIKey, db)

    def get_by_key_hash(self, key_hash: str) -> Optional[APIKey]:
        return self.get_by_field("key_hash", key_hash)

    def get_by_prefix(self, prefix: str) -> Optional[APIKey]:
        return self.get_by_field("prefix", prefix)

    def get_active_keys(self, user_id: int) -> List[APIKey]:
        return self.db.query(APIKey).filter(
            APIKey.user_id == user_id,
            APIKey.is_active == True,
        ).all()

    def deactivate(self, key_id: int) -> Optional[APIKey]:
        return self.update(key_id, {"is_active": False})


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(AuditLog, db)

    def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: int = None,
        endpoint: str = None,
        method: str = None,
        ip_address: str = None,
        user_agent: str = None,
        old_values: dict = None,
        new_values: dict = None,
        success: bool = True,
        error_message: str = None,
    ) -> AuditLog:
        return self.create({
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "endpoint": endpoint,
            "method": method,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "old_values": old_values,
            "new_values": new_values,
            "success": success,
            "error_message": error_message,
        })

    def get_by_user(self, user_id: int, limit: int = 100) -> List[AuditLog]:
        return self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    def get_by_resource(self, resource_type: str, resource_id: int, limit: int = 100) -> List[AuditLog]:
        return self.db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()


class WebhookRepository(BaseRepository[Webhook]):
    def __init__(self, db: Session):
        super().__init__(Webhook, db)

    def get_by_user(self, user_id: int) -> List[Webhook]:
        return self.db.query(Webhook).filter(
            Webhook.user_id == user_id,
            Webhook.is_active == True,
        ).all()

    def get_for_event(self, event_type: str) -> List[Webhook]:
        return self.db.query(Webhook).filter(
            Webhook.is_active == True,
        ).all()

    def increment_failure(self, webhook_id: int) -> Optional[Webhook]:
        webhook = self.get(webhook_id)
        if webhook:
            webhook.failure_count = (webhook.failure_count or 0) + 1
            if webhook.failure_count >= 5:
                webhook.is_active = False
            self.db.commit()
            self.db.refresh(webhook)
        return webhook
