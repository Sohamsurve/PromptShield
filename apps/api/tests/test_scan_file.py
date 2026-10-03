"""POST /v1/scan/file contract."""

from pathlib import Path

from fastapi.testclient import TestClient

from promptshield.api.app import app

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "fixtures"
client = TestClient(app)


def test_scan_file_html() -> None:
    path = FIXTURES / "F02_web_comment_reveal.html"
    with path.open("rb") as f:
        r = client.post(
            "/v1/scan/file",
            files={"file": ("F02.html", f, "text/html")},
            data={"source_type": "html", "trust": "3"},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["scan_id"]
    assert body["hidden_content_revealed"] is True or any(
        s.get("hidden_reason") for s in body.get("segments", [])
    )
