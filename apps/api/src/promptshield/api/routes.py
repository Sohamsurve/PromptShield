"""REST routes (README §6)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from promptshield.agent.aria import run_fixture
from promptshield.agent.fixtures import list_fixtures, load_fixture_text
from promptshield.domain import (
    OutputGuardRequest,
    OutputGuardResult,
    ScanRequest,
    ScanResult,
    SourceType,
    ToolCallRequest,
    ToolDecision,
    TrustLevel,
)
from promptshield.pipeline import POLICY_PATH, scan, scan_file_bytes

router = APIRouter()

# In-memory store
_SCANS: dict[str, ScanResult] = {}
_RUNS: dict[str, dict[str, Any]] = {}
_REPO_ROOT = Path(__file__).resolve().parents[5]
_EVAL_LATEST = _REPO_ROOT / "eval" / "reports" / "latest"


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics")
def metrics() -> dict[str, Any]:
    return {"scans_total": len(_SCANS), "runs_total": len(_RUNS)}


@router.post("/scan", response_model=ScanResult)
def post_scan(req: ScanRequest) -> ScanResult:
    result = scan(req, noop=False)
    _SCANS[result.scan_id] = result
    return result


def _infer_source_type(filename: str | None, declared: str | None) -> SourceType:
    if declared:
        return SourceType(declared)
    name = (filename or "").lower()
    if name.endswith((".html", ".htm")):
        return SourceType.html
    if name.endswith(".pdf"):
        return SourceType.pdf
    if name.endswith(".docx"):
        return SourceType.docx
    if name.endswith((".eml", ".mime")):
        return SourceType.email
    if name.endswith((".md", ".markdown")):
        return SourceType.markdown
    if name.endswith(".json"):
        return SourceType.api_response
    if name.endswith((".py", ".js", ".ts", ".java", ".go", ".rs")):
        return SourceType.source_code
    if name.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
        return SourceType.image
    return SourceType.text


@router.post("/scan/file", response_model=ScanResult)
async def post_scan_file(
    file: UploadFile = File(...),
    source_type: str | None = Form(default=None),
    trust: int = Form(default=3),
) -> ScanResult:
    data = await file.read()
    # Size cap — educational demo (10 MB)
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "file too large")
    st = _infer_source_type(file.filename, source_type)
    result = scan_file_bytes(data, st, trust=TrustLevel(trust))
    _SCANS[result.scan_id] = result
    return result


@router.get("/scans")
def list_scans(limit: int = 50) -> dict[str, Any]:
    items = list(_SCANS.values())[-limit:]
    items.reverse()
    return {"items": [s.model_dump() for s in items], "next_cursor": None}


@router.get("/scans/{scan_id}")
def get_scan(scan_id: str) -> ScanResult:
    if scan_id not in _SCANS:
        raise HTTPException(404, "scan not found")
    return _SCANS[scan_id]


@router.post("/guard/tool-call", response_model=ToolDecision)
def post_guard_tool_call(req: ToolCallRequest) -> ToolDecision:
    from promptshield.guard.tool_firewall import guard_tool_call as _guard

    return _guard(req)


@router.post("/guard/output", response_model=OutputGuardResult)
def post_guard_output(req: OutputGuardRequest) -> OutputGuardResult:
    from promptshield.guard.egress import guard_output as _guard

    return _guard(req)


@router.post("/guard/ingest", response_model=ScanResult)
def post_guard_ingest(body: dict[str, Any]) -> ScanResult:
    """RAG/document ingest scan (Phase 4)."""
    from promptshield.guard.ingest import ingest_scan

    content = body.get("content")
    if not content:
        raise HTTPException(400, "content required")
    st = SourceType(body.get("source_type", "markdown"))
    trust = TrustLevel(int(body.get("trust", 2)))
    return ingest_scan(content, source_type=st, trust=trust, session_id=body.get("session_id"))


@router.get("/eval/latest")
def eval_latest() -> dict[str, Any]:
    """Latest eval report + heatmap for dashboard Coverage/Eval screens."""
    report_path = _EVAL_LATEST / "report.json"
    heat_path = _EVAL_LATEST / "heatmap.json"
    if not report_path.exists():
        raise HTTPException(404, "No eval report yet. Run make eval-fast.")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if heat_path.exists():
        payload["heatmap"] = json.loads(heat_path.read_text(encoding="utf-8"))
    return payload


@router.get("/policy")
def get_policy() -> dict[str, Any]:
    return yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8")) or {}


@router.post("/policy/test")
def policy_test(body: dict[str, Any]) -> ScanResult:
    """Scan arbitrary text with current pipeline (hostile data — never execute)."""
    content = body.get("content") or ""
    if not content.strip():
        raise HTTPException(400, "content required")
    if len(content) > 100_000:
        raise HTTPException(413, "content too large")
    st = SourceType(body.get("source_type", "text"))
    trust = TrustLevel(int(body.get("trust", 1)))
    result = scan(
        ScanRequest(source_type=st, content=content, trust=trust, session_id=body.get("session_id")),
        noop=False,
    )
    _SCANS[result.scan_id] = result
    return result


@router.post("/policy/replay")
def policy_replay(body: dict[str, Any]) -> dict[str, Any]:
    """Estimate decision deltas for threshold tweaks against recent in-memory scans."""
    sources = body.get("sources") or {}
    deltas = {"allow": 0, "sanitize": 0, "quarantine": 0, "block": 0, "escalate": 0}
    changed = 0
    for s in list(_SCANS.values())[-500:]:
        st = "text"
        # Approximate: compare risk to proposed source thresholds
        cfg = sources.get(st) or sources.get("user_message") or {}
        block = float(cfg.get("block", 0.92))
        quarantine = float(cfg.get("quarantine", 0.70))
        if s.risk >= block:
            new = "block"
        elif s.risk >= quarantine:
            new = "quarantine"
        elif s.risk >= float(cfg.get("sanitize_span", 0.75)) * 0.9:
            new = "sanitize"
        else:
            new = "allow"
        old = s.decision.value
        if new != old:
            changed += 1
            deltas[new] = deltas.get(new, 0) + 1
    return {"n": min(len(_SCANS), 500), "changed": changed, "deltas": deltas}


@router.get("/demo/fixtures")
def demo_fixtures() -> list[dict[str, Any]]:
    return list_fixtures()


@router.post("/demo/run")
def demo_run(body: dict[str, Any]) -> dict[str, Any]:
    fixture_id = body.get("fixture_id")
    if not fixture_id:
        raise HTTPException(400, "fixture_id required")
    firewall = bool(body.get("firewall", True))
    text_scanning = bool(body.get("text_scanning", True))
    lanes = body.get("lanes")
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    results = []
    if lanes:
        for lane in lanes:
            results.append(
                run_fixture(fixture_id, firewall=(lane == "on"), text_scanning=text_scanning)
            )
    else:
        results.append(run_fixture(fixture_id, firewall=firewall, text_scanning=text_scanning))
    payload = {"run_id": run_id, "results": results}
    _RUNS[run_id] = payload
    return payload


@router.get("/demo/fixtures/{fixture_id}/content")
def fixture_content(fixture_id: str) -> dict[str, str]:
    try:
        return {"fixture_id": fixture_id, "content": load_fixture_text(fixture_id)}
    except KeyError as e:
        raise HTTPException(404, "fixture not found") from e
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@router.websocket("/ws/stream")
async def ws_stream(ws: WebSocket) -> None:
    await ws.accept()
    try:
        await ws.send_json({"type": "connected", "payload": {"channel": "stream"}})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        return


@router.websocket("/ws/runs/{run_id}")
async def ws_runs(ws: WebSocket, run_id: str) -> None:
    await ws.accept()
    try:
        payload = _RUNS.get(run_id, {"run_id": run_id, "results": []})
        await ws.send_json({"type": "run.completed", "run_id": run_id, "lane": None, "payload": payload})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        return
