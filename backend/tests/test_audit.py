"""Audit-logging wiring and /audit/logs endpoint tests."""
import uuid


def _register_and_login(client, prefix="audit"):
    n = uuid.uuid4().hex[:8]
    email = f"{prefix}_{n}@example.com"
    password = "S3cret-pass"
    client.post(
        "/auth/register",
        json={"email": email, "username": f"{prefix}_{n}", "password": password},
    )
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return email, password, {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_register_and_login_audited(client, user):
    r = client.get("/audit/logs", headers=user.headers)
    assert r.status_code == 200
    entries = r.json()["items"]
    actions = [(e["action"], e["resource_type"], e["success"]) for e in entries]
    assert ("CREATE", "user", True) in actions
    assert ("LOGIN", "user", True) in actions


def test_failed_login_logged(client, user):
    client.post(
        "/auth/login", json={"email": user.email, "password": "wrong-password"}
    )
    entries = client.get(
        "/audit/logs?limit=100", headers=user.headers
    ).json()["items"]
    failures = [e for e in entries if e["action"] == "LOGIN" and not e["success"]]
    assert failures, "expected a failed LOGIN audit entry"
    assert failures[0]["error_message"] == "Invalid email or password"


def test_password_change_audited(client, user):
    r = client.put(
        "/auth/password",
        json={"current_password": user.password, "new_password": "NewSecret999"},
        headers=user.headers,
    )
    assert r.status_code == 200
    entries = client.get("/audit/logs?limit=100", headers=user.headers).json()["items"]
    pw_updates = [
        e
        for e in entries
        if e["action"] == "UPDATE" and (e.get("new_values") or {}).get("field") == "password"
    ]
    assert pw_updates


def test_agent_and_task_create_audited(client, auth_headers):
    client.post(
        "/agents/",
        json={"name": f"a_{uuid.uuid4().hex[:6]}", "capabilities": ["research"]},
        headers=auth_headers,
    )
    client.post(
        "/tasks/",
        json={"name": f"t_{uuid.uuid4().hex[:6]}", "priority": "medium"},
        headers=auth_headers,
    )
    entries = client.get("/audit/logs?limit=100", headers=auth_headers).json()["items"]
    assert any(e["action"] == "CREATE" and e["resource_type"] == "agent" for e in entries)
    assert any(e["action"] == "CREATE" and e["resource_type"] == "task" for e in entries)


def test_agent_delete_audited(client, make_agent, auth_headers):
    agent = make_agent(auth_headers)
    r = client.delete(f"/agents/{agent['id']}", headers=auth_headers)
    assert r.status_code == 200
    entries = client.get("/audit/logs?limit=100", headers=auth_headers).json()["items"]
    deletes = [
        e for e in entries
        if e["action"] == "DELETE" and e["resource_type"] == "agent"
        and e["resource_id"] == agent["id"]
    ]
    assert deletes
    assert deletes[0]["old_values"]["name"] == agent["name"]


def test_api_key_ops_audited(client, auth_headers):
    r = client.post("/auth/api-keys", json={"name": "audited"}, headers=auth_headers)
    assert r.status_code == 201
    key_id = r.json()["id"]
    client.delete(f"/auth/api-keys/{key_id}", headers=auth_headers)
    entries = client.get("/audit/logs?limit=100", headers=auth_headers).json()["items"]
    assert any(
        e["action"] == "CREATE" and e["resource_type"] == "api_key"
        and e["resource_id"] == key_id
        for e in entries
    )
    assert any(
        e["action"] == "DELETE" and e["resource_type"] == "api_key"
        and e["resource_id"] == key_id
        for e in entries
    )


def test_audit_requires_auth(client):
    assert client.get("/audit/logs").status_code == 401


def test_audit_scoped_to_own_user(client):
    _, _, headers_a = _register_and_login(client, "aud_a")
    me = client.get("/auth/me", headers=headers_a).json()

    _, _, headers_b = _register_and_login(client, "aud_b")
    r = client.get("/audit/logs?limit=100", headers=headers_b)
    assert r.status_code == 200
    items = r.json()["items"]
    assert items, "user B should have register/login entries"
    assert all(e["user_id"] != me["id"] for e in items)


def test_audit_action_filter(client, user):
    client.get("/auth/me", headers=user.headers)
    r = client.get("/audit/logs?action=LOGIN", headers=user.headers)
    assert r.status_code == 200
    items = r.json()["items"]
    assert items
    assert all(e["action"] == "LOGIN" for e in items)


def test_audit_total_and_pagination(client, auth_headers):
    r = client.get("/audit/logs?limit=1&skip=0", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) <= 1
    assert body["total"] >= 1
