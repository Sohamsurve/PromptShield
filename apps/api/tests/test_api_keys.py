"""Bearer keys: the owner creates them, a caller sees only their own scans."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _client(monkeypatch, tmp_path, **env):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'keys.db'}")
    monkeypatch.setenv("PROMPTSHIELD_POLICY_DIR", str(tmp_path / "pol"))
    monkeypatch.setenv("PROMPTSHIELD_POLICY", "template")
    monkeypatch.setenv("JUDGE_FORCE_OFFLINE", "1")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    from promptshield.api import persist
    from promptshield.api.app import app

    persist.reset_connection_for_tests()
    return TestClient(app)


def test_owner_creates_key_once_and_list_hides_the_secret(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="1")
    created = client.post("/v1/keys", json={"name": "Notebook agent"})
    assert created.status_code == 200
    body = created.json()
    token = body["token"]
    assert token.startswith("ps_")
    assert body["role"] == "user"
    listed = client.get("/v1/keys")
    assert listed.status_code == 200
    assert token not in listed.text
    assert body["key_id"] in listed.text
    assert "key_hash" not in listed.text


def test_user_key_scans_are_private_to_that_key(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="1")
    first = client.post("/v1/keys", json={"name": "First caller"}).json()["token"]
    second = client.post("/v1/keys", json={"name": "Second caller"}).json()["token"]
    scan = client.post(
        "/v1/scan",
        json={"content": "Summarise the quarterly product report.", "source_type": "text"},
        headers={"authorization": f"Bearer {first}"},
    )
    assert scan.status_code == 200
    scan_id = scan.json()["scan_id"]
    mine = client.get("/v1/scans", headers={"authorization": f"Bearer {first}"})
    assert scan_id in mine.text
    theirs = client.get("/v1/scans", headers={"authorization": f"Bearer {second}"})
    assert scan_id not in theirs.text
    hidden = client.get(f"/v1/scans/{scan_id}", headers={"authorization": f"Bearer {second}"})
    assert hidden.status_code == 404
    owner_view = client.get("/v1/scans")
    assert scan_id in owner_view.text
    me = client.get("/v1/me", headers={"authorization": f"Bearer {first}"})
    assert me.status_code == 200
    assert me.json()["role"] == "user"
    assert me.json()["scan_count"] == 1
    assert first not in me.text


def test_user_key_cannot_create_keys_or_change_policy(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="1")
    token = client.post("/v1/keys", json={"name": "Caller"}).json()["token"]
    headers = {"authorization": f"Bearer {token}"}
    assert client.post("/v1/keys", json={"name": "nope"}, headers=headers).status_code == 403
    assert client.get("/v1/keys", headers=headers).status_code == 403
    assert client.post("/v1/policy/reset", headers=headers).status_code == 403


def test_revoked_and_unknown_keys_fail_when_demo_is_off(monkeypatch, tmp_path):
    client = _client(
        monkeypatch,
        tmp_path,
        DEMO_MODE="0",
        PROMPTSHIELD_API_KEY="owner-key-not-a-secret",
    )
    owner = {"authorization": "Bearer owner-key-not-a-secret"}
    created = client.post("/v1/keys", json={"name": "Laptop"}, headers=owner)
    assert created.status_code == 200
    token = created.json()["token"]
    key_id = created.json()["key_id"]
    assert "owner-key-not-a-secret" not in created.text
    ok = client.post(
        "/v1/scan",
        json={"content": "Summarise the quarterly product report.", "source_type": "text"},
        headers={"authorization": f"Bearer {token}"},
    )
    assert ok.status_code == 200
    assert client.post("/v1/keys/{key_id}/revoke".format(key_id=key_id), headers=owner).status_code == 200
    denied = client.post(
        "/v1/scan",
        json={"content": "Summarise the quarterly product report.", "source_type": "text"},
        headers={"authorization": f"Bearer {token}"},
    )
    assert denied.status_code == 401
    unknown = client.post(
        "/v1/scan",
        json={"content": "hello", "source_type": "text"},
        headers={"authorization": "Bearer ps_not-a-real-key"},
    )
    assert unknown.status_code == 401
    assert token not in denied.text


def test_fixed_owner_sign_in_and_extra_admin_key(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="1")
    health = client.get("/v1/healthz")
    assert health.json()["owner_sign_in"] == "demo"
    assert "promptshield-owner" not in health.text
    me = client.get("/v1/me", headers={"authorization": "Bearer promptshield-owner"})
    assert me.status_code == 200
    assert me.json()["role"] == "admin"
    assert "promptshield-owner" not in me.text
    created = client.post(
        "/v1/keys",
        json={"name": "Second owner", "role": "admin"},
        headers={"authorization": "Bearer promptshield-owner"},
    )
    assert created.status_code == 200
    assert created.json()["role"] == "admin"
    admin_token = created.json()["token"]
    assert client.get("/v1/keys", headers={"authorization": f"Bearer {admin_token}"}).status_code == 200
    assert admin_token not in client.get("/v1/keys").text


def test_revoked_key_is_rejected_even_in_demo_mode(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="1")
    created = client.post("/v1/keys", json={"name": "Temp"}).json()
    assert client.post(f"/v1/keys/{created['key_id']}/revoke").status_code == 200
    denied = client.post(
        "/v1/scan",
        json={"content": "Summarise the quarterly product report.", "source_type": "text"},
        headers={"authorization": f"Bearer {created['token']}"},
    )
    assert denied.status_code == 401
    open_call = client.post(
        "/v1/scan",
        json={"content": "Summarise the quarterly product report.", "source_type": "text"},
    )
    assert open_call.status_code == 200
