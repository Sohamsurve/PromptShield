from fastapi.testclient import TestClient

from promptshield.api.app import app

client = TestClient(app)


def test_healthz() -> None:
    r = client.get("/v1/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_openapi_available() -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    body = r.json()
    assert body["info"]["title"] == "PromptShield API"
