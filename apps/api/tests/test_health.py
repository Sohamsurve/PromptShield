from fastapi.testclient import TestClient

from promptshield.api.app import app

client = TestClient(app)


def test_healthz() -> None:
    r = client.get("/v1/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "judge_mode" in body
    assert "judge_model" in body
    assert "llm_provider" in body
    assert "api_key_configured" in body
    # Never leak secrets via healthz
    blob = str(body).lower()
    assert "sk-" not in blob
    assert "api_key" not in body or isinstance(body["api_key_configured"], bool)


def test_openapi_available() -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    body = r.json()
    assert body["info"]["title"] == "PromptShield API"
