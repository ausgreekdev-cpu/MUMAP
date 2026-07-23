import pytest


class TestRegister:
    def test_register_success(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "securepassword123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["username"] == "newuser"
        assert "id" in data

    def test_register_duplicate_email(self, client, test_user):
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "username": "different",
            "password": "password123",
        })
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_duplicate_username(self, client, test_user):
        response = client.post("/api/v1/auth/register", json={
            "email": "different@example.com",
            "username": "testuser",
            "password": "password123",
        })
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]


class TestLogin:
    def test_login_success(self, client, test_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"

    def test_login_wrong_password(self, client, test_user):
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password",
        })
        assert response.status_code == 401


class TestGetMe:
    def test_get_me_success(self, client, test_user, auth_headers):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_get_me_no_auth(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalidtoken"
        })
        assert response.status_code == 401
