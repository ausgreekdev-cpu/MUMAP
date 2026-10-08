import uuid


def test_agent_crud_with_llm_config(client, auth_headers, make_agent):
    name = f"crud_{uuid.uuid4().hex[:6]}"
    created = make_agent(
        auth_headers,
        name=name,
        role="analyst",
        model_provider="openai",
        model_name="gpt-4o-mini",
        system_prompt="You are a test agent.",
        temperature=0.2,
        max_tokens=512,
    )
    assert created["name"] == name
    assert created["model_provider"] == "openai"
    assert created["model_name"] == "gpt-4o-mini"
    assert created["system_prompt"] == "You are a test agent."
    assert created["temperature"] == 0.2
    assert created["max_tokens"] == 512

    agent_id = created["id"]

    r = client.get(f"/agents/{agent_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["model_provider"] == "openai"

    r = client.get("/agents/", headers=auth_headers)
    assert r.status_code == 200
    assert any(a["id"] == agent_id for a in r.json()["agents"])

    r = client.put(
        f"/agents/{agent_id}",
        json={"model_name": "gpt-4o", "temperature": 0.9},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["model_name"] == "gpt-4o"
    assert r.json()["temperature"] == 0.9
    assert r.json()["system_prompt"] == "You are a test agent."

    r = client.delete(f"/agents/{agent_id}", headers=auth_headers)
    assert r.status_code == 200
    assert client.get(f"/agents/{agent_id}", headers=auth_headers).status_code == 404


def test_agent_invalid_provider_rejected(client, auth_headers, make_agent):
    r = client.post(
        "/agents/",
        json={"name": f"bad_{uuid.uuid4().hex[:6]}", "model_provider": "gemini"},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert "provider" in r.json()["detail"].lower()

    agent = make_agent(auth_headers)
    r = client.put(
        f"/agents/{agent['id']}",
        json={"model_provider": "gemini"},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert "provider" in r.json()["detail"].lower()


def test_agents_require_auth(client):
    assert client.get("/agents/").status_code == 401
    assert client.post("/agents/", json={"name": "x"}).status_code == 401
