import uuid


def test_usage_summary_records_chat_tokens(
    client, auth_headers, make_agent, mock_llm, openai_configured
):
    agent = make_agent(
        auth_headers,
        model_provider="openai",
        model_name="gpt-4o-mini",
        system_prompt="Test.",
    )
    r = client.post(
        f"/execution/agents/{agent['id']}/chat",
        json={"message": "record usage please"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text

    r = client.get("/usage/summary", headers=auth_headers)
    assert r.status_code == 200, r.text
    summary = r.json()
    assert summary["total_tokens"] >= 42
    assert summary["total_cost"] >= 0
    assert "by_type" in summary
    assert summary["by_type"]


def test_usage_costs_by_model(client, auth_headers, make_agent, mock_llm, openai_configured):
    agent = make_agent(
        auth_headers, model_provider="openai", model_name="gpt-4o-mini", system_prompt="T."
    )
    client.post(
        f"/execution/agents/{agent['id']}/chat",
        json={"message": "hi"},
        headers=auth_headers,
    )
    r = client.get("/usage/costs/by-model", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_cost"] >= 0
    assert "gpt-4o-mini" in body["by_model"]


def test_billing_plans_require_auth_and_return_plans(client, auth_headers):
    assert client.get("/usage/billing/plans").status_code == 401
    r = client.get("/usage/billing/plans", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    plans = body["plans"] if isinstance(body, dict) else body
    names = {p["name"].lower() for p in plans}
    assert "free" in names
    assert "pro" in names


def test_usage_check_limits(client, auth_headers):
    r = client.get("/usage/check", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "allowed" in body
    assert body["allowed"] is True
    assert "remaining_tokens" in body


def test_usage_requires_auth(client):
    assert client.get("/usage/summary").status_code == 401
    assert client.get("/usage/records").status_code == 401
