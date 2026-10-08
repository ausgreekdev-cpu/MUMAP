import uuid


def test_register_login_me(client):
    n = uuid.uuid4().hex[:8]
    email = f"auth_{n}@example.com"

    r = client.post(
        "/auth/register",
        json={"email": email, "username": f"auth_{n}", "password": "S3cret-pass"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == email

    r = client.post("/auth/login", json={"email": email, "password": "S3cret-pass"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_duplicate_register_rejected(client, user):
    r = client.post(
        "/auth/register",
        json={
            "email": user.email,
            "username": f"other_{uuid.uuid4().hex[:6]}",
            "password": "S3cret-pass",
        },
    )
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"]


def test_wrong_password_rejected(client, user):
    r = client.post("/auth/login", json={"email": user.email, "password": "wrong-pass"})
    assert r.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert r.status_code == 401
