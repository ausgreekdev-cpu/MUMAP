import uuid

from backend.database import SessionLocal
from backend.models.task import TaskLog


def test_task_logs_endpoint_returns_created_at(client, auth_headers):
    """Regression: task logs 500'd due to a timestamp/level schema mismatch."""
    n = uuid.uuid4().hex[:6]
    r = client.post(
        "/tasks/",
        json={
            "name": f"task_{n}",
            "description": "log regression task",
            "priority": "medium",
            "required_capabilities": ["research"],
        },
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    task_id = r.json()["id"]

    db = SessionLocal()
    try:
        db.add(
            TaskLog(
                task_id=task_id,
                level="INFO",
                event="created",
                message="task created",
                data={},
            )
        )
        db.commit()
    finally:
        db.close()

    r = client.get(f"/tasks/{task_id}/logs", headers=auth_headers)
    assert r.status_code == 200, r.text
    logs = r.json()
    assert len(logs) == 1
    assert logs[0]["event"] == "created"
    assert logs[0]["level"] == "INFO"
    assert "created_at" in logs[0]
    assert "timestamp" not in logs[0]


def test_task_logs_require_auth(client):
    assert client.get("/tasks/1/logs").status_code == 401


def test_task_auto_assign_and_cancel(client, auth_headers, make_agent):
    cap = f"cap_{uuid.uuid4().hex[:8]}"
    agent = make_agent(auth_headers, capabilities=[cap])
    r = client.post(
        "/tasks/",
        json={
            "name": f"auto_{uuid.uuid4().hex[:6]}",
            "description": "assign me",
            "priority": "high",
            "required_capabilities": [cap],
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    task_id = r.json()["id"]

    r = client.post(f"/tasks/{task_id}/auto-assign", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["assigned_to"] == agent["id"]

    r = client.post(f"/tasks/{task_id}/cancel", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
