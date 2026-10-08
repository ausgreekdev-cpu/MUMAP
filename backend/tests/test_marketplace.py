def test_templates_list_and_seed(client, auth_headers):
    r = client.get("/marketplace/templates", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 6
    names = {t["name"] for t in body["templates"]}
    assert {"Research Pro", "Code Reviewer", "Content Writer"} <= names
    for t in body["templates"]:
        assert t["price_label"]
        assert t["capabilities"]
        assert t["icon_key"]


def test_templates_search_and_category_filter(client, auth_headers):
    r = client.get(
        "/marketplace/templates",
        params={"search": "code"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    names = [t["name"] for t in r.json()["templates"]]
    assert names == ["Code Reviewer"]

    r = client.get(
        "/marketplace/templates",
        params={"category": "Writing"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert [t["name"] for t in r.json()["templates"]] == ["Content Writer"]


def test_install_creates_configured_agent(client, auth_headers):
    r = client.get("/marketplace/templates", headers=auth_headers)
    template = next(t for t in r.json()["templates"] if t["name"] == "Research Pro")

    r = client.post(
        f"/marketplace/templates/{template['id']}/install",
        json={},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    agent_id = body["agent_id"]
    assert body["agent_name"] == "Research Pro"
    assert body["installation"]["template_id"] == template["id"]

    r = client.get(f"/agents/{agent_id}", headers=auth_headers)
    assert r.status_code == 200
    agent = r.json()
    assert agent["model_provider"] == "openai"
    assert agent["model_name"] == "gpt-4o-mini"
    assert agent["system_prompt"]
    assert "research" in agent["capabilities"]
    assert agent["role"] == "researcher"

    r = client.post(
        f"/marketplace/templates/{template['id']}/install",
        json={},
        headers=auth_headers,
    )
    assert r.status_code == 400
    assert "already installed" in r.json()["detail"].lower()


def test_installed_list_and_installs_counter(client, auth_headers):
    r = client.get("/marketplace/templates", headers=auth_headers)
    template = next(t for t in r.json()["templates"] if t["name"] == "Data Analyst")
    before = template["installs_count"]

    client.post(
        f"/marketplace/templates/{template['id']}/install",
        json={},
        headers=auth_headers,
    )

    r = client.get("/marketplace/installed", headers=auth_headers)
    assert r.status_code == 200
    ids = [i["template_id"] for i in r.json()["installations"]]
    assert template["id"] in ids

    r = client.get(f"/marketplace/templates/{template['id']}", headers=auth_headers)
    assert r.json()["installs_count"] == before + 1


def test_marketplace_requires_auth(client):
    assert client.get("/marketplace/templates").status_code == 401
    assert client.get("/marketplace/installed").status_code == 401
    assert (
        client.post("/marketplace/templates/1/install", json={}).status_code == 401
    )


def test_install_unknown_template_404(client, auth_headers):
    r = client.post(
        "/marketplace/templates/999999/install", json={}, headers=auth_headers
    )
    assert r.status_code == 404
