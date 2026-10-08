import uuid

from backend.config import settings


def test_chat_success_with_mocked_llm(
    client, auth_headers, make_agent, mock_llm, openai_configured
):
    agent = make_agent(
        auth_headers,
        model_provider="openai",
        model_name="gpt-4o-mini",
        system_prompt="You are a test agent.",
    )

    r = client.post(
        f"/execution/agents/{agent['id']}/chat",
        json={
            "message": "second question",
            "history": [
                {"role": "user", "content": "first question"},
                {"role": "assistant", "content": "first answer"},
            ],
        },
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["response"] == "Mocked response"
    assert body["tokens_used"] == 42
    assert body["conversation_id"].startswith(f"conv_{agent['id']}_")

    call_kwargs = mock_llm.await_args.kwargs
    messages = call_kwargs["messages"]
    roles = [m["role"] for m in messages]
    assert roles == ["system", "user", "assistant", "user"]
    assert messages[0]["content"].startswith("You are a test agent.")
    assert messages[-1]["content"] == "second question"


def test_chat_history_capped_at_20(
    client, auth_headers, make_agent, mock_llm, openai_configured
):
    agent = make_agent(auth_headers, model_provider="openai", system_prompt="Test.")
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
        for i in range(30)
    ]
    r = client.post(
        f"/execution/agents/{agent['id']}/chat",
        json={"message": "latest", "history": history},
        headers=auth_headers,
    )
    assert r.status_code == 200
    messages = mock_llm.await_args.kwargs["messages"]
    # system + last 20 history + current message
    assert len(messages) == 22


def test_chat_without_api_key_returns_503(client, auth_headers, make_agent):
    old = settings.OPENAI_API_KEY
    settings.OPENAI_API_KEY = None
    try:
        agent = make_agent(auth_headers, model_provider="openai", system_prompt="Hi.")
        r = client.post(
            f"/execution/agents/{agent['id']}/chat",
            json={"message": "hello"},
            headers=auth_headers,
        )
        assert r.status_code == 503
        assert "OPENAI_API_KEY" in r.json()["detail"]
    finally:
        settings.OPENAI_API_KEY = old


def test_chat_without_llm_config_returns_400(client, auth_headers, make_agent):
    agent = make_agent(auth_headers)
    r = client.post(
        f"/execution/agents/{agent['id']}/chat",
        json={"message": "hello"},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert "LLM configuration" in r.json()["detail"]


def test_chat_requires_auth(client):
    r = client.post("/execution/agents/1/chat", json={"message": "hi"})
    assert r.status_code == 401


def test_chat_not_found(client, auth_headers):
    r = client.post(
        "/execution/agents/999999/chat",
        json={"message": "hi"},
        headers=auth_headers,
    )
    assert r.status_code == 404
