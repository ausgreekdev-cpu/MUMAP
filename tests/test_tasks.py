import pytest


class TestCreateTask:
    def test_create_task_success(self, client, auth_headers):
        response = client.post("/api/v1/tasks/", json={
            "name": "TestTask",
            "description": "A test task",
            "priority": "high",
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "TestTask"
        assert data["priority"] == "high"
        assert data["status"] == "pending"

    def test_create_task_no_auth(self, client):
        response = client.post("/api/v1/tasks/", json={
            "name": "UnauthorizedTask",
        })
        assert response.status_code == 401


class TestListTasks:
    def test_list_tasks_empty(self, client, auth_headers):
        response = client.get("/api/v1/tasks/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_list_tasks_with_data(self, client, auth_headers):
        client.post("/api/v1/tasks/", json={"name": "Task1"}, headers=auth_headers)
        client.post("/api/v1/tasks/", json={"name": "Task2"}, headers=auth_headers)

        response = client.get("/api/v1/tasks/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 2

    def test_list_tasks_filter_status(self, client, auth_headers):
        client.post("/api/v1/tasks/", json={"name": "Task1"}, headers=auth_headers)

        response = client.get("/api/v1/tasks/?status=pending", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1

        response = client.get("/api/v1/tasks/?status=completed", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestGetTask:
    def test_get_task_success(self, client, auth_headers):
        create_resp = client.post("/api/v1/tasks/", json={"name": "GetTask"}, headers=auth_headers)
        task_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "GetTask"

    def test_get_task_not_found(self, client, auth_headers):
        response = client.get("/api/v1/tasks/99999", headers=auth_headers)
        assert response.status_code == 404


class TestTaskOperations:
    def test_complete_task(self, client, auth_headers):
        create_resp = client.post("/api/v1/tasks/", json={"name": "CompleteTask"}, headers=auth_headers)
        task_id = create_resp.json()["id"]

        agent_resp = client.post("/api/v1/agents/", json={
            "name": "CompleteAgent",
            "capabilities": [],
        }, headers=auth_headers)
        agent_id = agent_resp.json()["id"]

        client.post(f"/api/v1/tasks/{task_id}/assign?agent_id={agent_id}", headers=auth_headers)
        client.post(f"/api/v1/tasks/{task_id}/complete", headers=auth_headers, json={})

        response = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
        assert response.json()["status"] == "completed"

    def test_cancel_task(self, client, auth_headers):
        create_resp = client.post("/api/v1/tasks/", json={"name": "CancelTask"}, headers=auth_headers)
        task_id = create_resp.json()["id"]

        response = client.post(f"/api/v1/tasks/{task_id}/cancel", headers=auth_headers)
        assert response.status_code == 200

        get_resp = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
        assert get_resp.json()["status"] == "cancelled"

    def test_retry_task(self, client, auth_headers):
        create_resp = client.post("/api/v1/tasks/", json={"name": "RetryTask"}, headers=auth_headers)
        task_id = create_resp.json()["id"]

        client.post(f"/api/v1/tasks/{task_id}/fail", headers=auth_headers, json={}, params={"error_message": "test error"})

        response = client.post(f"/api/v1/tasks/{task_id}/retry", headers=auth_headers)
        assert response.status_code == 200

        get_resp = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
        assert get_resp.json()["status"] == "pending"
        assert get_resp.json()["retry_count"] == 1
