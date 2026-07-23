import pytest


class TestRoot:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "version" in data

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]

    def test_ready_endpoint(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["ready"] is True
