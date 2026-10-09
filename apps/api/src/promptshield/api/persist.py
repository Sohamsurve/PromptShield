"""SQLite persistence for scans, tool decisions, and demo runs (README §4 / §5.12).

Uses DATABASE_URL (sqlite:///… only for demo). Configurable retention via
PROMPTSHIELD_RETENTION_DAYS (default 14) and PROMPTSHIELD_RETENTION_MAX (default 5000).
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from promptshield.domain import ScanResult, ToolDecision

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _db_path() -> Path:
    url = (os.getenv("DATABASE_URL") or "sqlite:///./promptshield.db").strip()
    if url.startswith("sqlite:///"):
        raw = unquote(url[len("sqlite:///") :])
        p = Path(raw)
        if not p.is_absolute():
            # Resolve relative to repo apps/api (cwd when running uvicorn)
            p = Path.cwd() / p
        return p
    if url.startswith("sqlite://"):
        # sqlite:///:memory: or sqlite:///absolute
        parsed = urlparse(url)
        path = unquote(parsed.path or "")
        if path in {"", "/", ":memory:"} or path.endswith(":memory:"):
            return Path(":memory:")
        return Path(path)
    # Fallback: treat as filesystem path
    return Path(url)


def _retention_days() -> int:
    try:
        return max(1, int(os.getenv("PROMPTSHIELD_RETENTION_DAYS") or "14"))
    except ValueError:
        return 14


def _retention_max() -> int:
    try:
        return max(100, int(os.getenv("PROMPTSHIELD_RETENTION_MAX") or "5000"))
    except ValueError:
        return 5000


def connect() -> sqlite3.Connection:
    global _conn
    with _lock:
        if _conn is not None:
            return _conn
        path = _db_path()
        if str(path) != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(path), check_same_thread=False)
        if str(path) != ":memory:":
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _init_schema(_conn)
        return _conn


def reset_connection_for_tests() -> None:
    """Close connection so next connect() picks up a new DATABASE_URL (tests)."""
    global _conn
    with _lock:
        if _conn is not None:
            try:
                _conn.close()
            except Exception:
                pass
            _conn = None


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS scans (
          scan_id TEXT PRIMARY KEY,
          created_at REAL NOT NULL,
          decision TEXT NOT NULL,
          risk REAL NOT NULL,
          payload TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_scans_created ON scans(created_at);
        CREATE TABLE IF NOT EXISTS tool_decisions (
          id TEXT PRIMARY KEY,
          created_at REAL NOT NULL,
          tool TEXT,
          decision TEXT,
          payload TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS runs (
          run_id TEXT PRIMARY KEY,
          created_at REAL NOT NULL,
          payload TEXT NOT NULL
        );
        """
    )
    conn.commit()


def _prune(conn: sqlite3.Connection) -> None:
    cutoff = time.time() - _retention_days() * 86400
    for table in ("scans", "tool_decisions", "runs"):
        conn.execute(f"DELETE FROM {table} WHERE created_at < ?", (cutoff,))
    # Cap rows
    for table, pk in (("scans", "scan_id"), ("tool_decisions", "id"), ("runs", "run_id")):
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if n > _retention_max():
            excess = n - _retention_max()
            conn.execute(
                f"""
                DELETE FROM {table} WHERE {pk} IN (
                  SELECT {pk} FROM {table} ORDER BY created_at ASC LIMIT ?
                )
                """,
                (excess,),
            )
    conn.commit()


def purge() -> dict[str, int]:
    """Delete stored scans, tool decisions, and demo runs."""
    conn = connect()
    counts: dict[str, int] = {}
    with _lock:
        for table in ("scans", "tool_decisions", "runs"):
            counts[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
    return counts


_SECRET = __import__("re").compile(r"sk-[A-Za-z0-9_\-]{8,}")
_EMAIL = __import__("re").compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def _mask_text(value: str) -> str:
    value = _SECRET.sub("[secret]", value)
    value = _EMAIL.sub("[email]", value)
    return value[:200]


def _mask_payload(payload: dict[str, Any]) -> dict[str, Any]:
    findings = payload.get("findings")
    if isinstance(findings, list):
        for finding in findings:
            if isinstance(finding, dict) and isinstance(finding.get("evidence"), str):
                finding["evidence"] = _mask_text(finding["evidence"])
    return payload


def save_scan(result: ScanResult) -> None:
    conn = connect()
    payload = _mask_payload(result.model_dump(mode="json"))
    with _lock:
        conn.execute(
            "INSERT OR REPLACE INTO scans(scan_id, created_at, decision, risk, payload) VALUES (?,?,?,?,?)",
            (result.scan_id, time.time(), result.decision.value, float(result.risk), json.dumps(payload)),
        )
        _prune(conn)


def get_scan(scan_id: str) -> ScanResult | None:
    conn = connect()
    row = conn.execute("SELECT payload FROM scans WHERE scan_id = ?", (scan_id,)).fetchone()
    if not row:
        return None
    return ScanResult.model_validate(json.loads(row["payload"]))


def list_scans(limit: int = 50) -> list[ScanResult]:
    conn = connect()
    rows = conn.execute(
        "SELECT payload FROM scans ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [ScanResult.model_validate(json.loads(r["payload"])) for r in rows]


def scans_count() -> int:
    conn = connect()
    return int(conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0])


def save_tool_decision(decision: ToolDecision) -> None:
    import uuid

    conn = connect()
    payload = decision.model_dump(mode="json")
    tid = f"td_{uuid.uuid4().hex[:12]}"
    with _lock:
        conn.execute(
            "INSERT INTO tool_decisions(id, created_at, tool, decision, payload) VALUES (?,?,?,?,?)",
            (tid, time.time(), payload.get("tool") or "", str(payload.get("decision") or ""), json.dumps(payload)),
        )
        _prune(conn)


def save_run(run_id: str, payload: dict[str, Any]) -> None:
    conn = connect()
    with _lock:
        conn.execute(
            "INSERT OR REPLACE INTO runs(run_id, created_at, payload) VALUES (?,?,?)",
            (run_id, time.time(), json.dumps(payload)),
        )
        _prune(conn)


def get_run(run_id: str) -> dict[str, Any] | None:
    conn = connect()
    row = conn.execute("SELECT payload FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if not row:
        return None
    return json.loads(row["payload"])


def runs_count() -> int:
    conn = connect()
    return int(conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0])
