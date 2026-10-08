import os
import sys
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_TMP = tempfile.mkdtemp(prefix="map_tests_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("ANTHROPIC_API_KEY", None)

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.llm.adapter import LLMAdapter


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def user(client):
    n = uuid.uuid4().hex[:8]
    email = f"user_{n}@example.com"
    username = f"user_{n}"
    password = "S3cret-pass"
    r = client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert r.status_code == 200, r.text
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return SimpleNamespace(
        email=email,
        username=username,
        password=password,
        token=token,
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest.fixture()
def auth_headers(user):
    return user.headers


@pytest.fixture()
def make_agent(client):
    def _make(headers, **overrides):
        payload = {
            "name": f"agent_{uuid.uuid4().hex[:8]}",
            "description": "test agent",
            "capabilities": ["research"],
        }
        payload.update(overrides)
        r = client.post("/agents/", json=payload, headers=headers)
        assert r.status_code == 200, r.text
        return r.json()

    return _make


@pytest.fixture()
def mock_llm():
    mock = AsyncMock(
        return_value=SimpleNamespace(
            content="Mocked response",
            tokens_used=42,
            tool_calls=[],
            latency_ms=15,
        )
    )
    with patch.object(LLMAdapter, "complete", new=mock):
        yield mock


@pytest.fixture()
def openai_configured():
    from backend.config import settings

    old = settings.OPENAI_API_KEY
    settings.OPENAI_API_KEY = "sk-test-key"
    yield
    settings.OPENAI_API_KEY = old
