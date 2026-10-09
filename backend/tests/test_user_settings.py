import uuid


def _register_and_login(client):
    n = uuid.uuid4().hex[:8]
    email = f"settings_{n}@example.com"
    username = f"settings_{n}"
    r = client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": "S3cret-pass"},
    )
    assert r.status_code == 200, r.text
    r = client.post("/auth/login", json={"email": email, "password": "S3cret-pass"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return email, username, {"Authorization": f"Bearer {token}"}


def test_update_profile(client, auth_headers, user):
    r = client.put(
        "/auth/profile",
        json={"username": f"renamed_{uuid.uuid4().hex[:6]}"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["username"].startswith("renamed_")
    assert r.json()["email"] == user.email


def test_update_profile_empty_body_rejected(client, auth_headers):
    r = client.put("/auth/profile", json={}, headers=auth_headers)
    assert r.status_code == 400
    assert "No fields" in r.json()["detail"]


def test_update_profile_duplicate_email_and_username(client, auth_headers, user):
    _, other_username, other_headers = _register_and_login(client)

    r = client.put(
        "/auth/profile", json={"email": user.email}, headers=other_headers
    )
    assert r.status_code == 400
    assert "Email" in r.json()["detail"]

    r = client.put(
        "/auth/profile", json={"username": user.username}, headers=other_headers
    )
    assert r.status_code == 400
    assert "Username" in r.json()["detail"]


def test_update_profile_allows_own_values(client, auth_headers, user):
    r = client.put(
        "/auth/profile",
        json={"email": user.email, "username": user.username},
        headers=auth_headers,
    )
    assert r.status_code == 200


def test_update_profile_invalid_email(client, auth_headers):
    r = client.put(
        "/auth/profile", json={"email": "not-an-email"}, headers=auth_headers
    )
    assert r.status_code == 422


def test_update_profile_requires_auth(client):
    assert client.put("/auth/profile", json={"username": "someone"}).status_code == 401


def test_change_password_flow(client, auth_headers, user):
    r = client.put(
        "/auth/password",
        json={"current_password": "wrong-pass", "new_password": "NewSecret123"},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert "Current password" in r.json()["detail"]

    r = client.put(
        "/auth/password",
        json={"current_password": user.password, "new_password": "short"},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert "at least 8" in r.json()["detail"]

    r = client.put(
        "/auth/password",
        json={"current_password": user.password, "new_password": "NewSecret123"},
        headers=auth_headers,
    )
    assert r.status_code == 200

    assert (
        client.post(
            "/auth/login", json={"email": user.email, "password": user.password}
        ).status_code
        == 401
    )
    r = client.post(
        "/auth/login", json={"email": user.email, "password": "NewSecret123"}
    )
    assert r.status_code == 200


def test_preferences_defaults(client, auth_headers):
    r = client.get("/auth/preferences", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {
        "task_completed": True,
        "task_failed": True,
        "agent_offline": False,
        "weekly_summary": True,
    }


def test_preferences_persist_and_merge(client, auth_headers):
    r = client.put(
        "/auth/preferences",
        json={"agent_offline": True, "weekly_summary": False},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["agent_offline"] is True
    assert body["weekly_summary"] is False
    assert body["task_completed"] is True

    r = client.get("/auth/preferences", headers=auth_headers)
    assert r.json()["agent_offline"] is True
    assert r.json()["weekly_summary"] is False


def test_preferences_reject_unknown_and_non_bool(client, auth_headers):
    r = client.put(
        "/auth/preferences", json={"bogus_key": True}, headers=auth_headers
    )
    assert r.status_code == 400
    assert "bogus_key" in r.json()["detail"]

    r = client.put(
        "/auth/preferences", json={"task_failed": "yes"}, headers=auth_headers
    )
    assert r.status_code == 400
    assert "boolean" in r.json()["detail"]


def test_preferences_isolated_per_user(client, auth_headers):
    client.put(
        "/auth/preferences", json={"agent_offline": True}, headers=auth_headers
    )
    _, _, other_headers = _register_and_login(client)
    r = client.get("/auth/preferences", headers=other_headers)
    assert r.json()["agent_offline"] is False


def test_preferences_require_auth(client):
    assert client.get("/auth/preferences").status_code == 401
    assert (
        client.put("/auth/preferences", json={"task_failed": True}).status_code == 401
    )
