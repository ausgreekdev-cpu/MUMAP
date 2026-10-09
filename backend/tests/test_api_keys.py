"""API-key creation, authentication, and lifecycle tests."""
import uuid
from datetime import timedelta

from backend.utils import utcnow


def _create_key(client, headers, **overrides):
    payload = {"name": overrides.pop("name", "test-key"), **overrides}
    r = client.post("/auth/api-keys", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_key_returns_plaintext_once_and_prefix(client, auth_headers):
    body = _create_key(client, auth_headers, name="ci-key")

    assert body["key"].startswith("ma_")
    assert body["prefix"] == body["key"][:10]
    assert "key_hash" not in body
    assert body["is_active"] is True
    assert body["last_used_at"] is None

    listing = client.get("/auth/api-keys", headers=auth_headers)
    assert listing.status_code == 200
    assert all("key" not in item for item in listing.json())
    assert all("key_hash" not in item for item in listing.json())
    assert any(item["id"] == body["id"] for item in listing.json())


def test_api_key_authenticates_and_jwt_still_works(client, auth_headers):
    body = _create_key(client, auth_headers)
    key_headers = {"X-API-Key": body["key"]}

    r = client.get("/auth/me", headers=key_headers)
    assert r.status_code == 200, r.text
    key_user = r.json()

    r = client.get("/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["id"] == key_user["id"]


def test_api_key_updates_last_used_at(client, auth_headers):
    body = _create_key(client, auth_headers)
    r = client.get("/auth/me", headers={"X-API-Key": body["key"]})
    assert r.status_code == 200

    listing = client.get("/auth/api-keys", headers=auth_headers).json()
    used = next(item for item in listing if item["id"] == body["id"])
    assert used["last_used_at"] is not None


def test_no_credentials_401(client):
    assert client.get("/auth/me").status_code == 401


def test_garbage_api_key_401(client):
    r = client.get("/auth/me", headers={"X-API-Key": "ma_bogus_key_value"})
    assert r.status_code == 401


def test_create_key_requires_auth(client):
    r = client.post("/auth/api-keys", json={"name": "x"})
    assert r.status_code == 401


def test_revoked_key_401(client, auth_headers):
    body = _create_key(client, auth_headers)

    r = client.delete(f"/auth/api-keys/{body['id']}", headers=auth_headers)
    assert r.status_code == 200

    assert client.get("/auth/me", headers={"X-API-Key": body["key"]}).status_code == 401
    ids = [item["id"] for item in client.get("/auth/api-keys", headers=auth_headers).json()]
    assert body["id"] not in ids


def test_expired_key_401(client, auth_headers):
    body = _create_key(client, auth_headers, expires_at=(utcnow() + timedelta(days=1)).isoformat())
    assert client.get("/auth/me", headers={"X-API-Key": body["key"]}).status_code == 200

    from backend.database import SessionLocal
    from backend.models.user import APIKey

    db = SessionLocal()
    try:
        row = db.query(APIKey).filter(APIKey.id == body["id"]).first()
        row.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    r = client.get("/auth/me", headers={"X-API-Key": body["key"]})
    assert r.status_code == 401
    assert r.json()["detail"] == "API key expired"


def test_delete_other_users_key_404(client, user):
    other = _register(client)
    body = _create_key(client, user.headers)
    r = client.delete(f"/auth/api-keys/{body['id']}", headers=other)
    assert r.status_code == 404


def test_unknown_scope_400(client, auth_headers):
    r = client.post(
        "/auth/api-keys",
        json={"name": "scoped", "scopes": ["admin:all"]},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert "admin:all" in r.json()["detail"]


def test_expiry_in_past_rejected_400(client, auth_headers):
    r = client.post(
        "/auth/api-keys",
        json={"name": "past", "expires_at": (utcnow() - timedelta(days=1)).isoformat()},
        headers=auth_headers,
    )
    assert r.status_code == 400


def _register(client) -> dict:
    n = uuid.uuid4().hex[:8]
    client.post(
        "/auth/register",
        json={"email": f"k_{n}@example.com", "username": f"k_{n}", "password": "S3cret-pass"},
    )
    r = client.post(
        "/auth/login", json={"email": f"k_{n}@example.com", "password": "S3cret-pass"}
    )
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
