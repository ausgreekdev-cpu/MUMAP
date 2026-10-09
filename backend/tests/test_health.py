def test_health_endpoint_shape(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("healthy", "degraded")
    assert "database" in body["checks"]
    assert "redis" in body["checks"]


def test_health_requires_no_auth(client):
    assert client.get("/health").status_code == 200
