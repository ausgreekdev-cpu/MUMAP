"""Rate-limit middleware tests (in-memory fallback; no Redis required)."""
from backend.services.cache import RateLimiter


def test_general_limit_returns_429_with_retry_after(client, user, rate_limit_enabled):
    from backend.config import settings

    old = settings.RATE_LIMIT_REQUESTS
    settings.RATE_LIMIT_REQUESTS = 3
    try:
        for _ in range(3):
            assert client.get("/auth/me", headers=user.headers).status_code == 200

        r = client.get("/auth/me", headers=user.headers)
        assert r.status_code == 429
        assert r.headers.get("Retry-After")
        assert "Rate limit" in r.json()["detail"]
    finally:
        settings.RATE_LIMIT_REQUESTS = old


def test_limit_is_per_identity(client, user, rate_limit_enabled):
    from backend.config import settings

    other = client.post(
        "/auth/register",
        json={
            "email": "rl_other@example.com",
            "username": "rl_other",
            "password": "S3cret-pass",
        },
    )
    assert other.status_code == 200
    r = client.post(
        "/auth/login",
        json={"email": "rl_other@example.com", "password": "S3cret-pass"},
    )
    other_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    old = settings.RATE_LIMIT_REQUESTS
    settings.RATE_LIMIT_REQUESTS = 2
    try:
        assert client.get("/auth/me", headers=user.headers).status_code == 200
        assert client.get("/auth/me", headers=user.headers).status_code == 200
        assert client.get("/auth/me", headers=user.headers).status_code == 429

        # A different identity is unaffected
        assert client.get("/auth/me", headers=other_headers).status_code == 200
    finally:
        settings.RATE_LIMIT_REQUESTS = old


def test_login_endpoint_rate_limited_per_ip(client, rate_limit_enabled):
    from backend.config import settings

    old = settings.RATE_LIMIT_AUTH_REQUESTS
    settings.RATE_LIMIT_AUTH_REQUESTS = 3
    try:
        for _ in range(3):
            client.post(
                "/auth/login",
                json={"email": "nobody@example.com", "password": "wrong"},
            )
        r = client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "wrong"},
        )
        assert r.status_code == 429
    finally:
        settings.RATE_LIMIT_AUTH_REQUESTS = old


def test_health_is_exempt(client, rate_limit_enabled):
    from backend.config import settings

    old = settings.RATE_LIMIT_REQUESTS
    settings.RATE_LIMIT_REQUESTS = 1
    try:
        client.get("/auth/me")
        r = client.get("/auth/me")
        assert r.status_code == 429

        assert client.get("/health").status_code == 200
    finally:
        settings.RATE_LIMIT_REQUESTS = old


def test_disabled_by_default_in_suite(client, user):
    from backend.config import settings

    old = settings.RATE_LIMIT_REQUESTS
    settings.RATE_LIMIT_REQUESTS = 1
    try:
        for _ in range(3):
            r = client.get("/auth/me", headers=user.headers)
            assert r.status_code == 200
    finally:
        settings.RATE_LIMIT_REQUESTS = old


def test_in_memory_limiter_unit():
    limiter = RateLimiter()
    assert limiter.cache.enabled is False

    assert limiter.is_rate_limited("unit-key", max_requests=2, window=60) is False
    assert limiter.is_rate_limited("unit-key", max_requests=2, window=60) is False
    assert limiter.is_rate_limited("unit-key", max_requests=2, window=60) is True

    limited, retry_after = limiter.check("unit-check", max_requests=1, window=60)
    assert limited is False and retry_after >= 1
    limited, retry_after = limiter.check("unit-check", max_requests=1, window=60)
    assert limited is True

    assert limiter.get_remaining("unit-key", max_requests=5, window=60) == 2
