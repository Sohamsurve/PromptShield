"""A caller can create and revoke their own keys, and scans stay on the account."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _client(monkeypatch, tmp_path, **env):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'user-keys.db'}")
    monkeypatch.setenv("PROMPTSHIELD_POLICY_DIR", str(tmp_path / "pol"))
    monkeypatch.setenv("PROMPTSHIELD_POLICY", "template")
    monkeypatch.setenv("JUDGE_FORCE_OFFLINE", "1")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    from promptshield.api import persist
    from promptshield.api.app import app

    persist.reset_connection_for_tests()
    return TestClient(app)


def _signup(client: TestClient) -> dict:
    created = client.post(
        "/v1/auth/signup",
        json={"name": "Aria", "email": "aria@example.test", "password": "correct-horse"},
    )
    assert created.status_code == 200
    return created.json()


def test_caller_creates_a_key_and_the_list_hides_the_secret(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="1")
    account = _signup(client)
    headers = {"authorization": f"Bearer {account['token']}"}
    created = client.post("/v1/me/keys", json={"name": "Laptop", "role": "admin"}, headers=headers)
    assert created.status_code == 200
    body = created.json()
    assert body["token"].startswith("ps_")
    assert body["role"] == "user"
    listed = client.get("/v1/me/keys", headers=headers)
    assert listed.status_code == 200
    assert body["token"] not in listed.text
    items = listed.json()["items"]
    names = [item["name"] for item in items]
    assert "Laptop" in names
    assert "Aria" in names
    primary = [item for item in items if item["primary"]]
    assert len(primary) == 1
    assert primary[0]["name"] == "Aria"


def test_extra_key_scans_stay_on_the_account(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="0", PROMPTSHIELD_API_KEY="owner-key-not-a-secret")
    account = _signup(client)
    headers = {"authorization": f"Bearer {account['token']}"}
    extra = client.post("/v1/me/keys", json={"name": "CI"}, headers=headers).json()["token"]
    scan = client.post(
        "/v1/scan",
        json={"content": "Summarise the quarterly product report.", "source_type": "text"},
        headers={"authorization": f"Bearer {extra}"},
    )
    assert scan.status_code == 200
    scan_id = scan.json()["scan_id"]
    mine = client.get("/v1/scans", headers=headers)
    assert scan_id in mine.text
    other = client.post(
        "/v1/auth/signup",
        json={"name": "Other", "email": "other@example.test", "password": "correct-horse"},
    ).json()
    hidden = client.get("/v1/me/keys", headers={"authorization": f"Bearer {other['token']}"})
    assert "CI" not in hidden.text
    assert client.post("/v1/me/keys/key_missing/revoke", headers=headers).status_code == 404


def test_caller_can_open_the_playground_and_not_the_admin_controls(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="1")
    account = _signup(client)
    headers = {"authorization": f"Bearer {account['token']}"}
    ran = client.post(
        "/v1/demo/run",
        json={"fixture_id": "F01", "lanes": ["on"]},
        headers=headers,
    )
    assert ran.status_code == 200
    scan_id = ran.json()["results"][0]["scan"]["scan_id"]
    assert client.get(f"/v1/scans/{scan_id}", headers=headers).status_code == 200
    tested = client.post(
        "/v1/policy/test",
        json={"content": "Summarise the weekly notes for the team."},
        headers=headers,
    )
    assert tested.status_code == 200
    assert client.get(f"/v1/scans/{tested.json()['scan_id']}", headers=headers).status_code == 200
    assert client.get("/v1/eval/latest", headers=headers).status_code in {200, 404}
    assert client.post("/v1/policy/reset", headers=headers).status_code == 403
    assert client.post("/v1/eval/run", json={}, headers=headers).status_code == 403
    assert client.post("/v1/redteam/regression", json={"content": "x"}, headers=headers).status_code == 403


def test_caller_cannot_revoke_the_account_key_or_an_admin_key(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="1")
    account = _signup(client)
    headers = {"authorization": f"Bearer {account['token']}"}
    assert client.post(f"/v1/me/keys/{account['key_id']}/revoke", headers=headers).status_code == 400
    assert client.get("/v1/keys", headers=headers).status_code == 403
    assert client.post("/v1/me/keys", json={"name": "nope"}).status_code == 403
