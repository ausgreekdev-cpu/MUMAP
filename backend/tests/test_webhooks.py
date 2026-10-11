"""Webhook CRUD, signed delivery, and user-scoping tests."""
import hashlib
import hmac
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _register(client, prefix="wh"):
    n = uuid.uuid4().hex[:8]
    email = f"{prefix}_{n}@example.com"
    password = "S3cret-pass"
    client.post(
        "/auth/register",
        json={"email": email, "username": f"{prefix}_{n}", "password": password},
    )
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _create_webhook(client, headers, **overrides):
    payload = {
        "name": "test-hook",
        "url": "https://example.com/hook",
        "events": ["task.completed"],
        **overrides,
    }
    r = client.post("/webhooks", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
def mock_delivery():
    """Patch httpx.AsyncClient used by WebhookService; yield captured posts."""
    captured = []

    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=lambda url, **kw: captured.append((url, kw)) or mock_response)

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("backend.services.webhook.httpx.AsyncClient", return_value=mock_ctx):
        yield captured


def test_create_returns_secret_once_and_redacts_in_list(client, auth_headers):
    body = _create_webhook(client, auth_headers)
    assert body["secret"].startswith("whsec_")
    assert body["secret_set"] is True

    listing = client.get("/webhooks", headers=auth_headers).json()
    assert all("secret" not in item for item in listing)
    assert all(item["secret_set"] for item in listing)


def test_create_with_provided_secret(client, auth_headers):
    body = _create_webhook(client, auth_headers, secret="my-shared-secret")
    assert body["secret"] == "my-shared-secret"


def test_invalid_event_400(client, auth_headers):
    r = client.post(
        "/webhooks",
        json={"name": "bad", "url": "https://x.com/h", "events": ["nope.event"]},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert "nope.event" in r.json()["detail"]


def test_invalid_url_400(client, auth_headers):
    r = client.post(
        "/webhooks",
        json={"name": "bad", "url": "ftp://x.com/h", "events": ["task.failed"]},
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_delete_own_and_cross_user_404(client, auth_headers):
    body = _create_webhook(client, auth_headers)
    other = _register(client, "wh_other")

    assert client.delete(f"/webhooks/{body['id']}", headers=other).status_code == 404
    assert client.delete(f"/webhooks/{body['id']}", headers=auth_headers).status_code == 200
    assert client.get("/webhooks", headers=auth_headers).json() == []


def test_task_completed_triggers_signed_delivery(client, auth_headers, mock_delivery):
    body = _create_webhook(client, auth_headers, events=["task.completed"])

    r = client.post(
        "/tasks/",
        json={"name": "hook-task", "priority": "medium"},
        headers=auth_headers,
    )
    task_id = r.json()["id"]
    r = client.post(f"/tasks/{task_id}/complete", json={}, headers=auth_headers)
    assert r.status_code == 200, r.text

    assert len(mock_delivery) == 1
    url, kwargs = mock_delivery[0]
    assert url == "https://example.com/hook"
    assert kwargs["headers"]["X-Webhook-Event"] == "task.completed"

    payload = json.loads(kwargs["content"])
    assert payload["event"] == "task.completed"
    assert payload["data"]["id"] == task_id
    assert payload["data"]["name"] == "hook-task"

    expected = hmac.new(
        body["secret"].encode(), kwargs["content"].encode(), hashlib.sha256
    ).hexdigest()
    assert kwargs["headers"]["X-Webhook-Signature"] == f"sha256={expected}"


def test_delivery_is_user_scoped(client, mock_delivery):
    headers_a = _register(client, "wh_scopa")
    headers_b = _register(client, "wh_scopeb")

    hook_b = _create_webhook(client, headers_b, events=["task.completed"])

    r = client.post(
        "/tasks/",
        json={"name": "a-task", "priority": "low"},
        headers=headers_a,
    )
    task_id = r.json()["id"]
    client.post(f"/tasks/{task_id}/complete", json={}, headers=headers_a)

    urls = [url for url, _ in mock_delivery]
    assert hook_b["url"] not in urls


def test_agent_status_change_triggers(client, make_agent, auth_headers, mock_delivery):
    agent = make_agent(auth_headers)
    _create_webhook(
        client, auth_headers, events=["agent.status_changed"], url="https://example.com/agent"
    )

    r = client.post(
        f"/agents/{agent['id']}/status", params={"status": "busy"}, headers=auth_headers
    )
    assert r.status_code == 200

    assert len(mock_delivery) == 1
    url, kwargs = mock_delivery[0]
    assert url == "https://example.com/agent"
    payload = json.loads(kwargs["content"])
    assert payload["event"] == "agent.status_changed"
    assert payload["data"]["id"] == agent["id"]
    assert payload["data"]["status"] == "busy"


def test_test_endpoint_reports_success(client, auth_headers, mock_delivery):
    body = _create_webhook(client, auth_headers)
    r = client.post(f"/webhooks/{body['id']}/test", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"success": True}


def test_auto_disable_after_five_failures(client, auth_headers):
    body = _create_webhook(client, auth_headers)

    fail_response = MagicMock()
    fail_response.status_code = 500
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=fail_response)
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("backend.services.webhook.httpx.AsyncClient", return_value=mock_ctx):
        for _ in range(5):
            r = client.post(f"/webhooks/{body['id']}/test", headers=auth_headers)
            assert r.json() == {"success": False}

    listing = client.get("/webhooks", headers=auth_headers).json()
    hook = next(h for h in listing if h["id"] == body["id"])
    assert hook["is_active"] is False
    assert hook["failure_count"] == 5


def test_webhooks_require_auth(client):
    assert client.get("/webhooks").status_code == 401
    r = client.post(
        "/webhooks",
        json={"name": "x", "url": "https://x.com/h", "events": ["task.failed"]},
    )
    assert r.status_code == 401
