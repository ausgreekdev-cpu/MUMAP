import httpx
import hmac
import hashlib
import json
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from ..models.user import Webhook
from ..config import settings

logger = logging.getLogger(__name__)


class WebhookEvent:
    """Supported webhook events."""
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    AGENT_STATUS_CHANGED = "agent.status_changed"
    
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"
    
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    
    ALL = [
        AGENT_CREATED, AGENT_UPDATED, AGENT_DELETED, AGENT_STATUS_CHANGED,
        TASK_CREATED, TASK_ASSIGNED, TASK_COMPLETED, TASK_FAILED, TASK_CANCELLED,
        USER_CREATED, USER_UPDATED,
    ]


class WebhookService:
    """Service for sending webhook notifications."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_webhooks(self, event: str) -> list[Webhook]:
        """Get all active webhooks for a specific event."""
        webhooks = self.db.query(Webhook).filter(
            Webhook.is_active == True
        ).all()
        
        return [w for w in webhooks if event in (w.events or [])]
    
    def create_signature(self, payload: str, secret: str) -> str:
        """Create HMAC signature for webhook verification."""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def send_webhook(
        self,
        webhook: Webhook,
        event: str,
        data: dict,
    ) -> bool:
        """Send a webhook notification."""
        
        payload = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        
        payload_str = json.dumps(payload, default=str)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event,
            "X-Webhook-Timestamp": payload["timestamp"],
        }
        
        # Add signature if secret is configured
        if webhook.secret:
            signature = self.create_signature(payload_str, webhook.secret)
            headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        # Add custom headers
        if webhook.headers:
            headers.update(webhook.headers)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook.url,
                    content=payload_str,
                    headers=headers,
                )
                
                success = 200 <= response.status_code < 300
                
                if success:
                    webhook.last_triggered_at = datetime.utcnow()
                    webhook.failure_count = 0
                else:
                    webhook.failure_count += 1
                    logger.warning(f"Webhook failed: {webhook.url} returned {response.status_code}")
                
                # Disable webhook if too many failures
                if webhook.failure_count >= 5:
                    webhook.is_active = False
                    logger.warning(f"Webhook disabled due to failures: {webhook.url}")
                
                self.db.commit()
                return success
                
        except Exception as e:
            webhook.failure_count += 1
            if webhook.failure_count >= 5:
                webhook.is_active = False
            self.db.commit()
            logger.error(f"Webhook error: {str(e)}")
            return False
    
    async def trigger_event(self, event: str, data: dict) -> int:
        """Trigger event and send to all matching webhooks."""
        webhooks = self.get_active_webhooks(event)
        
        sent_count = 0
        for webhook in webhooks:
            try:
                success = await self.send_webhook(webhook, event, data)
                if success:
                    sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send webhook: {str(e)}")
        
        return sent_count


def get_webhook_service(db: Session) -> WebhookService:
    """Factory function for webhook service."""
    return WebhookService(db)
