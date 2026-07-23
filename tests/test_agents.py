import pytest


class TestCreateAgent:
    def test_create_agent_success(self, client, auth_headers):
        response = client.post("/api/v1/agents/", json={
            "name": "TestAgent",
            "description": "A test agent",
            "capabilities": ["math", "analysis"],
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "TestAgent"
        assert "math" in data["capabilities"]

    def test_create_agent_duplicate_name(self, client, auth_headers):
        client.post("/api/v1/agents/", json={
            "name": "DuplicateAgent",
        }, headers=auth_headers)

        response = client.post("/api/v1/agents/", json={
            "name": "DuplicateAgent",
        }, headers=auth_headers)
        assert response.status_code == 400

    def test_create_agent_no_auth(self, client):
        response = client.post("/api/v1/agents/", json={
            "name": "UnauthorizedAgent",
        })
        assert response.status_code == 401


class TestListAgents:
    def test_list_agents_empty(self, client, auth_headers):
        response = client.get("/api/v1/agents/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["agents"] == []

    def test_list_agents_with_data(self, client, auth_headers):
        client.post("/api/v1/agents/", json={"name": "Agent1"}, headers=auth_headers)
        client.post("/api/v1/agents/", json={"name": "Agent2"}, headers=auth_headers)

        response = client.get("/api/v1/agents/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2


class TestGetAgent:
    def test_get_agent_success(self, client, auth_headers):
        create_resp = client.post("/api/v1/agents/", json={
            "name": "GetAgent",
        }, headers=auth_headers)
        agent_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/agents/{agent_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "GetAgent"

    def test_get_agent_not_found(self, client, auth_headers):
        response = client.get("/api/v1/agents/99999", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateAgent:
    def test_update_agent_success(self, client, auth_headers):
        create_resp = client.post("/api/v1/agents/", json={
            "name": "UpdateAgent",
        }, headers=auth_headers)
        agent_id = create_resp.json()["id"]

        response = client.put(f"/api/v1/agents/{agent_id}", json={
            "description": "Updated description",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"


class TestDeleteAgent:
    def test_delete_agent_success(self, client, auth_headers):
        create_resp = client.post("/api/v1/agents/", json={
            "name": "DeleteAgent",
        }, headers=auth_headers)
        agent_id = create_resp.json()["id"]

        response = client.delete(f"/api/v1/agents/{agent_id}", headers=auth_headers)
        assert response.status_code == 204

        get_resp = client.get(f"/api/v1/agents/{agent_id}", headers=auth_headers)
        assert get_resp.status_code == 404


class TestAgentStatus:
    def test_update_status(self, client, auth_headers):
        create_resp = client.post("/api/v1/agents/", json={
            "name": "StatusAgent",
        }, headers=auth_headers)
        agent_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/agents/{agent_id}/status?status=busy",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_update_status_invalid(self, client, auth_headers):
        create_resp = client.post("/api/v1/agents/", json={
            "name": "InvalidStatusAgent",
        }, headers=auth_headers)
        agent_id = create_resp.json()["id"]

        response = client.post(
            f"/api/v1/agents/{agent_id}/status?status=invalid",
            headers=auth_headers,
        )
        assert response.status_code == 400
