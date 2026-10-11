import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User, Webhook
from ..schemas.webhook import WebhookCreate, WebhookCreated, WebhookResponse
from ..services.auth import get_current_user
from ..services.audit import get_audit_logger, request_context
from ..services.webhook import WebhookEvent, WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _to_response(
    webhook: Webhook, secret: Optional[str] = None
) -> "WebhookResponse | WebhookCreated":
    response = WebhookResponse.model_validate(webhook)
    response.secret_set = bool(webhook.secret)
    if secret is not None:
        return WebhookCreated(**response.model_dump(), secret=secret)
    return response


def _validate_events(events: list[str]) -> None:
    unknown = set(events) - set(WebhookEvent.ALL)
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown events: {', '.join(sorted(unknown))}",
        )


def _validate_url(url: str) -> None:
    if not url.lower().startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400, detail="URL must start with http:// or https://"
        )


@router.get("", response_model=list[WebhookResponse])
def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    webhooks = (
        db.query(Webhook)
        .filter(Webhook.user_id == current_user.id)
        .order_by(Webhook.created_at.desc())
        .all()
    )
    return [_to_response(w) for w in webhooks]


@router.post("", response_model=WebhookCreated, status_code=201)
def create_webhook(
    body: WebhookCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_events(body.events)
    _validate_url(body.url)

    secret = body.secret or f"whsec_{secrets.token_urlsafe(24)}"
    webhook = Webhook(
        user_id=current_user.id,
        name=body.name,
        url=body.url,
        secret=secret,
        events=body.events,
        headers=body.headers or {},
    )
    db.add(webhook)
    db.flush()
    get_audit_logger(db).log(
        action="CREATE",
        resource_type="webhook",
        resource_id=webhook.id,
        user_id=current_user.id,
        new_values={"name": webhook.name, "url": webhook.url, "events": body.events},
        **request_context(request),
    )
    db.commit()
    db.refresh(webhook)
    return _to_response(webhook, secret=secret)


@router.delete("/{webhook_id}")
def delete_webhook(
    webhook_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    webhook = (
        db.query(Webhook)
        .filter(Webhook.id == webhook_id, Webhook.user_id == current_user.id)
        .first()
    )
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    old_values = {"name": webhook.name, "url": webhook.url}
    db.delete(webhook)
    get_audit_logger(db).log(
        action="DELETE",
        resource_type="webhook",
        resource_id=webhook_id,
        user_id=current_user.id,
        old_values=old_values,
        **request_context(request),
    )
    db.commit()
    return {"message": "Webhook deleted"}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    webhook = (
        db.query(Webhook)
        .filter(Webhook.id == webhook_id, Webhook.user_id == current_user.id)
        .first()
    )
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    service = WebhookService(db)
    success = await service.send_webhook(
        webhook, "webhook.test", {"message": "Test delivery", "webhook_id": webhook.id}
    )
    return {"success": success}
