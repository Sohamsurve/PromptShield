"""Email accounts: sign up once, sign in later, scans stay on that account."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _client(monkeypatch, tmp_path, **env):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'accounts.db'}")
    monkeypatch.setenv("PROMPTSHIELD_POLICY_DIR", str(tmp_path / "pol"))
    monkeypatch.setenv("PROMPTSHIELD_POLICY", "template")
    monkeypatch.setenv("JUDGE_FORCE_OFFLINE", "1")
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    from promptshield.api import persist
    from promptshield.api.app import app

    persist.reset_connection_for_tests()
    return TestClient(app)


def test_signup_returns_a_key_once_and_hides_the_password(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="1")
    created = client.post(
        "/v1/auth/signup",
        json={"name": "Aria", "email": "Aria@Example.test", "password": "correct-horse"},
    )
    assert created.status_code == 200
    body = created.json()
    assert body["token"].startswith("ps_")
    assert body["role"] == "user"
    assert body["email"] == "aria@example.test"
    assert "correct-horse" not in created.text
    assert "password_hash" not in created.text
    me = client.get("/v1/me", headers={"authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200
    assert me.json()["role"] == "user"
    assert me.json()["name"] == "Aria"
    again = client.post(
        "/v1/auth/signup",
        json={"name": "Aria", "email": "aria@example.test", "password": "correct-horse"},
    )
    assert again.status_code == 409


def test_admin_sees_account_usage_and_a_caller_does_not(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="1")
    created = client.post(
        "/v1/auth/signup",
        json={"name": "Aria", "email": "aria@example.test", "password": "correct-horse"},
    )
    token = created.json()["token"]
    headers = {"authorization": f"Bearer {token}"}
    scanned = client.post(
        "/v1/scan",
        json={"content": "Summarise the quarterly product report.", "source_type": "text"},
        headers=headers,
    )
    assert scanned.status_code == 200
    listed = client.get("/v1/accounts")
    assert listed.status_code == 200
    body = listed.json()
    assert "password" not in listed.text
    assert "salt" not in listed.text
    row = next(item for item in body["items"] if item["email"] == "aria@example.test")
    assert row["name"] == "Aria"
    assert row["scans"] == 1
    assert row["keys_active"] >= 1
    assert sum(row["decisions"].values()) == 1
    hidden = client.get("/v1/accounts", headers=headers)
    assert hidden.status_code == 403


def test_login_session_sees_only_that_accounts_scans(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, DEMO_MODE="0", PROMPTSHIELD_API_KEY="owner-key-not-a-secret")
    signed = client.post(
        "/v1/auth/signup",
        json={"name": "Notebook", "email": "notebook@example.test", "password": "correct-horse"},
    )
    assert signed.status_code == 200
    api_key = signed.json()["token"]
    logged = client.post(
        "/v1/auth/login",
        json={"email": "notebook@example.test", "password": "correct-horse"},
    )
    assert logged.status_code == 200
    session = logged.json()["token"]
    assert session.startswith("ps_")
    assert session != api_key
    assert "correct-horse" not in logged.text
    headers = {"authorization": f"Bearer {session}"}
    scan = client.post(
        "/v1/scan",
        json={"content": "Summarise the quarterly product report.", "source_type": "text"},
        headers=headers,
    )
    assert scan.status_code == 200
    scan_id = scan.json()["scan_id"]
    mine = client.get("/v1/scans", headers={"authorization": f"Bearer {api_key}"})
    assert scan_id in mine.text
    wrong = client.post("/v1/auth/login", json={"email": "notebook@example.test", "password": "nope-nope"})
    assert wrong.status_code == 401
    short = client.post(
        "/v1/auth/signup",
        json={"name": "X", "email": "x@example.test", "password": "short"},
    )
    assert short.status_code == 400
