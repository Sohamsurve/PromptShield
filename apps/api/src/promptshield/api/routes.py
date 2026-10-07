"""REST routes (README §6)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, PlainTextResponse

from promptshield.agent.aria import run_fixture
from promptshield.agent.fixtures import list_fixtures, load_fixture_text
from promptshield.api import policy_store
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
from promptshield.pipeline import scan, scan_file_bytes

router = APIRouter()

# In-memory store (demo); policy versions are durable on disk
_SCANS: dict[str, ScanResult] = {}
_RUNS: dict[str, dict[str, Any]] = {}
_REDTEAM: list[dict[str, Any]] = []
_EVAL_RUNS: list[dict[str, Any]] = []
_REPO_ROOT = Path(__file__).resolve().parents[5]
_EVAL_LATEST = _REPO_ROOT / "eval" / "reports" / "latest"
_EVAL_REPORTS = _REPO_ROOT / "eval" / "reports"


@router.get("/healthz")
def healthz() -> dict[str, Any]:
    from promptshield.detect.judge import judge_config

    cfg = judge_config()
    return {
        "status": "ok",
        "judge_mode": cfg["judge_mode"],
        "judge_model": cfg["judge_model"] or "",
        "llm_provider": cfg["llm_provider"] or "",
        "api_key_configured": cfg["api_key_configured"],
        "judge_timeout_ms": cfg["timeout_ms"],
        "judge_reasoning_effort": cfg["reasoning_effort"] or "",
    }


@router.get("/metrics")
def metrics() -> PlainTextResponse:
    """Prometheus-style text exposition (README §6)."""
    payload = {
        "scans_total": len(_SCANS),
        "runs_total": len(_RUNS),
        "redteam_attempts_total": len(_REDTEAM),
    }
    lines = [
        "# HELP promptshield_scans_total Scans stored in process memory",
        "# TYPE promptshield_scans_total counter",
        f"promptshield_scans_total {payload['scans_total']}",
        "# HELP promptshield_runs_total Demo/arena runs stored",
        "# TYPE promptshield_runs_total counter",
        f"promptshield_runs_total {payload['runs_total']}",
        "# HELP promptshield_redteam_attempts_total Red-team attempts logged",
        "# TYPE promptshield_redteam_attempts_total counter",
        f"promptshield_redteam_attempts_total {payload['redteam_attempts_total']}",
    ]
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


@router.get("/metrics.json")
def metrics_json() -> dict[str, Any]:
    return {
        "scans_total": len(_SCANS),
        "runs_total": len(_RUNS),
        "redteam_attempts_total": len(_REDTEAM),
    }


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
    if name.endswith((".eml", ".mime", ".ics")):
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
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "file too large")
    st = _infer_source_type(file.filename, source_type)
    result = scan_file_bytes(data, st, trust=TrustLevel(trust))
    _SCANS[result.scan_id] = result
    return result


@router.get("/scans")
def list_scans(
    limit: int = Query(default=50, ge=1, le=500),
    cursor: str | None = None,
    decision: str | None = None,
    source_type: str | None = None,
    attack_type: str | None = None,
    q: str | None = None,
) -> dict[str, Any]:
    items = list(_SCANS.values())
    items.reverse()
    if decision:
        items = [s for s in items if s.decision.value == decision]
    if source_type:
        # ScanResult may not store source_type on root — filter via findings/evidence text
        items = [s for s in items if source_type in json.dumps(s.model_dump())]
    if attack_type:
        items = [
            s
            for s in items
            if any(attack_type == a.value for a in s.attack_types)
            or any(attack_type in [x.value for x in f.attack_types] for f in s.findings)
        ]
    if q:
        ql = q.lower()
        items = [
            s
            for s in items
            if ql in s.scan_id.lower()
            or ql in (s.sanitized_text or "").lower()
            or any(ql in (f.evidence or "").lower() for f in s.findings)
        ]
    start = 0
    if cursor:
        try:
            start = next(i for i, s in enumerate(items) if s.scan_id == cursor) + 1
        except StopIteration:
            start = 0
    page = items[start : start + limit]
    next_cursor = page[-1].scan_id if len(page) == limit and start + limit < len(items) else None
    return {"items": [s.model_dump() for s in page], "next_cursor": next_cursor}


@router.get("/scans/{scan_id}")
def get_scan(scan_id: str) -> ScanResult:
    if scan_id not in _SCANS:
        raise HTTPException(404, "scan not found")
    return _SCANS[scan_id]


@router.get("/scans/{scan_id}/xray")
def get_xray(scan_id: str) -> dict[str, Any]:
    """X-ray model (README §6.2) — derived from ScanResult segments/findings."""
    if scan_id not in _SCANS:
        raise HTTPException(404, "scan not found")
    s = _SCANS[scan_id]
    layers = []
    for f in s.findings:
        layers.append(
            {
                "detector": f.detector,
                "rule_id": f.rule_id,
                "reason_code": f.reason_code,
                "score": f.score,
                "span": list(f.span) if f.span else None,
                "segment_id": f.segment_id,
                "evidence": f.evidence,
            }
        )
    invisible = []
    for seg in s.segments:
        text = ""  # summaries only; chips from reason codes
        if any(ch in (seg.hidden_reason or "") for ch in ("zero_width", "bidi", "tag")):
            invisible.append({"segment": seg.id, "kind": seg.hidden_reason})
    pages = [
        {
            "page": 1,
            "image_url": f"/v1/scans/{scan_id}/pages/1.png",
            "boxes": [
                {"segment": f.segment_id, "span": list(f.span) if f.span else None}
                for f in s.findings
                if f.span
            ],
        }
    ]
    return {
        "scan_id": scan_id,
        "decision": s.decision.value,
        "risk": s.risk,
        "layers": layers,
        "decode_tree": [],
        "segments": [seg.model_dump() for seg in s.segments],
        "findings": [f.model_dump() for f in s.findings],
        "pages": pages,
        "invisible_chars": invisible,
        "sanitized_text": s.sanitized_text,
        "degraded": s.degraded,
    }


@router.get("/scans/{scan_id}/pages/{page}.png")
def get_page_image(scan_id: str, page: int) -> FileResponse:
    """Placeholder page image for X-ray (1×1 PNG) when OCR/page render unavailable."""
    if scan_id not in _SCANS:
        raise HTTPException(404, "scan not found")
    # Minimal valid 1x1 PNG
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
    )
    path = _REPO_ROOT / "apps" / "api" / "data" / "xray_pages" / f"{scan_id}_{page}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(png)
    return FileResponse(path, media_type="image/png")


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
    from promptshield.guard.ingest import ingest_scan

    content = body.get("content")
    if not content:
        raise HTTPException(400, "content required")
    st = SourceType(body.get("source_type", "markdown"))
    trust = TrustLevel(int(body.get("trust", 2)))
    return ingest_scan(content, source_type=st, trust=trust, session_id=body.get("session_id"))


@router.get("/eval/latest")
def eval_latest() -> dict[str, Any]:
    report_path = _EVAL_LATEST / "report.json"
    heat_path = _EVAL_LATEST / "heatmap.json"
    if not report_path.exists():
        raise HTTPException(404, "No eval report yet. Run make eval-fast.")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    if heat_path.exists():
        payload["heatmap"] = json.loads(heat_path.read_text(encoding="utf-8"))
    return payload


@router.get("/eval/heatmap")
def eval_heatmap() -> dict[str, Any]:
    heat_path = _EVAL_LATEST / "heatmap.json"
    if not heat_path.exists():
        raise HTTPException(404, "No heatmap yet. Run make eval-fast.")
    return json.loads(heat_path.read_text(encoding="utf-8"))


@router.get("/eval/runs")
def eval_runs() -> dict[str, Any]:
    runs = list(_EVAL_RUNS)
    # Also surface on-disk report directories
    disk = []
    if _EVAL_REPORTS.exists():
        for p in sorted(_EVAL_REPORTS.iterdir(), reverse=True):
            if p.is_dir() and (p / "report.json").exists():
                disk.append({"id": p.name, "path": str(p.relative_to(_REPO_ROOT))})
    return {"in_memory": runs, "on_disk": disk[:20]}


@router.post("/eval/run")
def eval_run(body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Start a fast eval asynchronously (subprocess); returns eval_run_id."""
    import subprocess
    import threading

    body = body or {}
    mode = body.get("mode", "fast")
    eval_run_id = f"eval_{uuid.uuid4().hex[:8]}"
    rec = {"eval_run_id": eval_run_id, "mode": mode, "status": "running"}
    _EVAL_RUNS.insert(0, rec)

    def _job() -> None:
        try:
            cmd = [
                "uv",
                "--directory",
                str(_REPO_ROOT / "apps" / "api"),
                "run",
                "python",
                str(_REPO_ROOT / "eval" / "run_eval.py"),
                "--fast" if mode != "full" else "--full",
            ]
            subprocess.run(cmd, cwd=str(_REPO_ROOT), check=False, capture_output=True)
            rec["status"] = "completed"
        except Exception as e:  # noqa: BLE001
            rec["status"] = "failed"
            rec["error"] = type(e).__name__

    threading.Thread(target=_job, daemon=True).start()
    return {"eval_run_id": eval_run_id, "status": "running", "mode": mode}


@router.get("/policy")
def get_policy() -> dict[str, Any]:
    pol = policy_store.current_policy()
    # Top-level policy fields for existing clients; versions for durable history UI
    out = dict(pol)
    out["_versions"] = policy_store.list_versions()[:20]
    return out


@router.put("/policy")
def put_policy(body: dict[str, Any]) -> dict[str, Any]:
    """Durable policy save with version history (demo-local disk)."""
    note = str(body.pop("note", "") or "")
    # Accept either wrapped {policy: {...}} or raw policy body
    pol = body.get("policy") if isinstance(body.get("policy"), dict) else body
    if not isinstance(pol, dict) or not pol:
        raise HTTPException(400, "policy object required")
    meta = policy_store.save_policy(pol, note=note)
    return {"ok": True, **meta, "versions": policy_store.list_versions()[:10]}


@router.get("/policy/versions/{version}")
def policy_version(version: int) -> dict[str, Any]:
    try:
        return policy_store.get_version(version)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@router.get("/policy/diff")
def policy_diff(a: int = Query(...), b: int = Query(...)) -> dict[str, Any]:
    try:
        return policy_store.diff_versions(a, b)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@router.post("/policy/test")
def policy_test(body: dict[str, Any]) -> ScanResult:
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
@router.post("/policy/simulate")
def policy_simulate(body: dict[str, Any]) -> dict[str, Any]:
    """Replay recent scans under draft source thresholds → decision deltas."""
    sources = body.get("sources") or {}
    deltas = {"allow": 0, "sanitize": 0, "quarantine": 0, "block": 0, "escalate": 0}
    changed = 0
    for s in list(_SCANS.values())[-500:]:
        cfg = sources.get("text") or sources.get("user_message") or {}
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


_ACTED_DECISIONS = {"sanitize", "quarantine", "block", "escalate"}


def _redteam_is_attack(text: str, body: dict[str, Any]) -> bool:
    """Attack inputs only. Benign/HN labels never count as leaderboard bypasses."""
    if "is_attack" in body and body["is_attack"] is not None:
        return bool(body["is_attack"])
    label = str(body.get("label") or "").strip().lower()
    if label in {"benign", "hard_negative", "negative"}:
        return False
    if label == "attack":
        return True
    # Unlabeled: signature / cue shaped → attack; otherwise treat as non-attack.
    from promptshield.detect.signatures import SignatureEngine

    if SignatureEngine().scan(text, segment_id="rt"):
        return True
    cues = (
        r"(?i)ignore.{0,40}(previous|prior|all).{0,30}instructions",
        r"(?i)reveal.{0,20}system prompt",
        r"(?i)\b(jailbreak|you are now|act as)\b",
        r"(?i)forward.{0,30}emails?",
        r"(?i)from now on|add this to your memory",
    )
    import re

    return any(re.search(p, text) for p in cues)


@router.post("/redteam/attempt")
def redteam_attempt(body: dict[str, Any]) -> dict[str, Any]:
    """Scan free-text (or fixture) attack attempt; log for leaderboard."""
    text = body.get("text") or ""
    fixture_id = body.get("fixture_id")
    target = body.get("target", "aria")
    if fixture_id:
        try:
            text = load_fixture_text(fixture_id)
        except Exception as e:
            raise HTTPException(404, f"fixture not found: {e}") from e
    if not text.strip():
        raise HTTPException(400, "text or fixture_id required")
    if len(text) > 100_000:
        raise HTTPException(413, "content too large")
    result = scan(
        ScanRequest(source_type=SourceType.text, content=text, trust=TrustLevel.T3),
        noop=False,
    )
    _SCANS[result.scan_id] = result
    is_attack = _redteam_is_attack(text, body)
    acted = result.decision.value in _ACTED_DECISIONS
    # Bypass = attack input that was not acted on (allow). Benign allow is never a bypass.
    bypass = bool(is_attack) and not acted
    entry = {
        "id": f"rt_{uuid.uuid4().hex[:8]}",
        "target": target,
        "scan_id": result.scan_id,
        "decision": result.decision.value,
        "risk": result.risk,
        "is_attack": is_attack,
        "acted": acted,
        "bypass": bypass,
        "flagged": bool(result.findings),
        "preview": text[:160],
    }
    _REDTEAM.insert(0, entry)
    return {"attempt": entry, "scan": result.model_dump()}


@router.get("/redteam/leaderboard")
def redteam_leaderboard() -> dict[str, Any]:
    """De-duplicated attempts; bypasses = attack inputs not acted on."""
    seen: set[str] = set()
    rows = []
    for e in _REDTEAM:
        key = e.get("preview") or e["id"]
        if key in seen:
            continue
        seen.add(key)
        rows.append(e)
    bypasses = [r for r in rows if r.get("bypass")]
    return {
        "n": len(rows),
        "bypasses": len(bypasses),
        "items": rows[:100],
        "bypass_definition": "attack_input_and_not_acted",
    }


@router.websocket("/ws/stream")
async def ws_stream(ws: WebSocket) -> None:
    await ws.accept()
    try:
        await ws.send_json({"type": "connected", "payload": {"channel": "stream"}})
        # Emit a heartbeat snapshot of recent scan count
        await ws.send_json(
            {
                "type": "degraded" if False else "scan.completed",
                "payload": {"scans_total": len(_SCANS)},
            }
        )
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        return


@router.websocket("/ws/runs/{run_id}")
async def ws_runs(ws: WebSocket, run_id: str) -> None:
    await ws.accept()
    try:
        payload = _RUNS.get(run_id)
        if payload is None:
            await ws.send_json({"type": "run.completed", "run_id": run_id, "lane": None, "payload": {"results": []}})
        else:
            for res in payload.get("results") or []:
                lane = res.get("lane")
                await ws.send_json(
                    {
                        "type": "agent.step",
                        "run_id": run_id,
                        "lane": lane,
                        "payload": {"steps": res.get("steps") or []},
                    }
                )
                await ws.send_json(
                    {
                        "type": "run.completed",
                        "run_id": run_id,
                        "lane": lane,
                        "payload": res,
                    }
                )
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        return
