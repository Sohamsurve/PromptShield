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
from promptshield.neutralize.redact import safe_alternative

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
        CREATE TABLE IF NOT EXISTS api_keys (
          key_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          prefix TEXT NOT NULL,
          key_hash TEXT NOT NULL,
          role TEXT NOT NULL,
          created_at REAL NOT NULL,
          revoked INTEGER NOT NULL DEFAULT 0
        );
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
        CREATE TABLE IF NOT EXISTS accounts (
          email TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          password_hash TEXT NOT NULL,
          salt TEXT NOT NULL,
          key_id TEXT NOT NULL,
          created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY,
          key_id TEXT NOT NULL,
          created_at REAL NOT NULL,
          revoked INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(scans)")}
    if "owner_key_id" not in columns:
        conn.execute("ALTER TABLE scans ADD COLUMN owner_key_id TEXT")
    key_columns = {row[1] for row in conn.execute("PRAGMA table_info(api_keys)")}
    if "owner_email" not in key_columns:
        conn.execute("ALTER TABLE api_keys ADD COLUMN owner_email TEXT")
    conn.execute(
        """
        UPDATE api_keys
        SET owner_email = (
          SELECT email FROM accounts WHERE accounts.key_id = api_keys.key_id
        )
        WHERE owner_email IS NULL
          AND EXISTS (SELECT 1 FROM accounts WHERE accounts.key_id = api_keys.key_id)
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


def save_scan(result: ScanResult, owner_key_id: str | None = None) -> None:
    conn = connect()
    payload = _mask_payload(result.model_dump(mode="json"))
    with _lock:
        conn.execute(
            "INSERT OR REPLACE INTO scans(scan_id, created_at, decision, risk, payload, owner_key_id) VALUES (?,?,?,?,?,?)",
            (
                result.scan_id,
                time.time(),
                result.decision.value,
                float(result.risk),
                json.dumps(payload),
                owner_key_id,
            ),
        )
        _prune(conn)


def _with_alternative(result: ScanResult) -> ScanResult:
    """Older stored scans predate safe_alternative. Fill it from the redacted text."""
    stored = result.safe_alternative or ""
    if stored and "CANARY" not in stored.upper() and "adversarial" not in stored.lower():
        return result
    alt = safe_alternative(result.decision.value, result.sanitized_text)
    if not alt:
        return result
    return result.model_copy(update={"safe_alternative": alt})


def get_scan(scan_id: str) -> ScanResult | None:
    found = get_scan_owner(scan_id)
    return found[0] if found else None


def get_scan_owner(scan_id: str) -> tuple[ScanResult, str | None] | None:
    conn = connect()
    row = conn.execute(
        "SELECT payload, owner_key_id FROM scans WHERE scan_id = ?",
        (scan_id,),
    ).fetchone()
    if not row:
        return None
    return _with_alternative(ScanResult.model_validate(json.loads(row["payload"]))), row["owner_key_id"]


def list_scans(limit: int = 50, owner_key_id: str | None = None) -> list[ScanResult]:
    conn = connect()
    if owner_key_id is None:
        rows = conn.execute(
            "SELECT payload FROM scans ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT payload FROM scans WHERE owner_key_id = ? ORDER BY created_at DESC LIMIT ?",
            (owner_key_id, limit),
        ).fetchall()
    return [_with_alternative(ScanResult.model_validate(json.loads(r["payload"]))) for r in rows]


def scans_count_for(owner_key_id: str) -> int:
    conn = connect()
    return int(
        conn.execute("SELECT COUNT(*) FROM scans WHERE owner_key_id = ?", (owner_key_id,)).fetchone()[0]
    )


def scans_count() -> int:
    conn = connect()
    return int(conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0])


def list_account_usage() -> list[dict[str, Any]]:
    """Account name, email, key counts, and scan totals. No password material."""
    conn = connect()
    accounts = conn.execute(
        "SELECT email, name, key_id, created_at FROM accounts ORDER BY created_at DESC"
    ).fetchall()
    items: list[dict[str, Any]] = []
    for account in accounts:
        email = str(account["email"])
        key_id = str(account["key_id"])
        prefix_row = conn.execute("SELECT prefix FROM api_keys WHERE key_id = ?", (key_id,)).fetchone()
        keys = conn.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN revoked = 0 THEN 1 ELSE 0 END) AS active
            FROM api_keys
            WHERE owner_email = ?
            """,
            (email,),
        ).fetchone()
        decisions = conn.execute(
            """
            SELECT decision, COUNT(*) AS n, MAX(created_at) AS last_at
            FROM scans
            WHERE owner_key_id = ?
               OR owner_key_id IN (SELECT key_id FROM api_keys WHERE owner_email = ?)
            GROUP BY decision
            """,
            (key_id, email),
        ).fetchall()
        by_decision = {str(row["decision"]): int(row["n"]) for row in decisions}
        last_values = [float(row["last_at"]) for row in decisions if row["last_at"] is not None]
        items.append(
            {
                "email": email,
                "name": str(account["name"]),
                "prefix": str(prefix_row["prefix"]) if prefix_row else "",
                "created_at": float(account["created_at"]),
                "keys_active": int(keys["active"] or 0) if keys else 0,
                "keys_total": int(keys["total"] or 0) if keys else 0,
                "scans": sum(by_decision.values()),
                "last_scan_at": max(last_values) if last_values else None,
                "decisions": by_decision,
            }
        )
    return items


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


def hash_token(token: str) -> str:
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()


def create_api_key(name: str, role: str = "user", owner_email: str | None = None) -> dict[str, Any]:
    """Insert a caller key. The plaintext token is returned only from this call."""
    import secrets

    if role not in {"user", "admin"}:
        raise ValueError("role")
    token = "ps_" + secrets.token_urlsafe(32)
    key_id = "key_" + secrets.token_hex(6)
    prefix = token[:12]
    now = time.time()
    conn = connect()
    with _lock:
        conn.execute(
            "INSERT INTO api_keys(key_id, name, prefix, key_hash, role, created_at, revoked, owner_email) VALUES (?,?,?,?,?,?,0,?)",
            (key_id, name[:80], prefix, hash_token(token), role, now, owner_email),
        )
        conn.commit()
    return {
        "key_id": key_id,
        "name": name[:80],
        "prefix": prefix,
        "role": role,
        "created_at": now,
        "token": token,
    }


def list_api_keys(owner_email: str | None = None) -> list[dict[str, Any]]:
    conn = connect()
    account_key = ""
    if owner_email:
        account = conn.execute("SELECT key_id FROM accounts WHERE email = ?", (owner_email,)).fetchone()
        if account:
            account_key = str(account["key_id"])
        rows = conn.execute(
            """
            SELECT key_id, name, prefix, role, created_at, revoked
            FROM api_keys
            WHERE owner_email = ?
            ORDER BY created_at DESC
            """,
            (owner_email,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT key_id, name, prefix, role, created_at, revoked FROM api_keys ORDER BY created_at DESC"
        ).fetchall()
    return [
        {
            "key_id": row["key_id"],
            "name": row["name"],
            "prefix": row["prefix"],
            "role": row["role"],
            "created_at": row["created_at"],
            "revoked": bool(row["revoked"]),
            "primary": bool(account_key) and row["key_id"] == account_key,
        }
        for row in rows
    ]


def revoke_api_key(key_id: str) -> bool:
    conn = connect()
    with _lock:
        cur = conn.execute("UPDATE api_keys SET revoked = 1 WHERE key_id = ?", (key_id,))
        conn.execute("UPDATE sessions SET revoked = 1 WHERE key_id = ?", (key_id,))
        conn.commit()
        return cur.rowcount > 0


def account_email_for_key(key_id: str) -> str | None:
    conn = connect()
    row = conn.execute("SELECT email FROM accounts WHERE key_id = ?", (key_id,)).fetchone()
    if row:
        return str(row["email"])
    owned = conn.execute("SELECT owner_email FROM api_keys WHERE key_id = ?", (key_id,)).fetchone()
    if owned and owned["owner_email"]:
        return str(owned["owner_email"])
    return None


def revoke_account_key(key_id: str, owner_email: str) -> str:
    """Revoke one key that belongs to the account. The signup key stays."""
    conn = connect()
    account = conn.execute("SELECT key_id FROM accounts WHERE email = ?", (owner_email,)).fetchone()
    if account and str(account["key_id"]) == key_id:
        return "primary"
    row = conn.execute(
        "SELECT owner_email FROM api_keys WHERE key_id = ?",
        (key_id,),
    ).fetchone()
    if row is None or str(row["owner_email"] or "") != owner_email:
        return "missing"
    if revoke_api_key(key_id):
        return "ok"
    return "missing"


def _account_principal(row: sqlite3.Row) -> dict[str, Any]:
    """Extra keys on an account still store scans on that account."""
    owner_email = str(row["owner_email"] or "")
    key_id = str(row["key_id"])
    if owner_email:
        account = connect().execute(
            "SELECT key_id FROM accounts WHERE email = ?",
            (owner_email,),
        ).fetchone()
        if account:
            key_id = str(account["key_id"])
    return {
        "role": row["role"],
        "key_id": key_id,
        "name": row["name"],
        "prefix": row["prefix"],
    }


def lookup_api_key(token: str) -> dict[str, Any] | None:
    import hmac

    if not token:
        return None
    digest = hash_token(token)
    conn = connect()
    rows = conn.execute(
        "SELECT key_id, name, prefix, role, revoked, key_hash, owner_email FROM api_keys WHERE revoked = 0"
    ).fetchall()
    for row in rows:
        if hmac.compare_digest(str(row["key_hash"]), digest):
            return _account_principal(row)
    sessions = conn.execute(
        """
        SELECT s.token_hash, k.key_id, k.name, k.prefix, k.role
        FROM sessions s
        JOIN api_keys k ON k.key_id = s.key_id
        WHERE s.revoked = 0 AND k.revoked = 0
        """
    ).fetchall()
    for row in sessions:
        if hmac.compare_digest(str(row["token_hash"]), digest):
            return {
                "role": row["role"],
                "key_id": row["key_id"],
                "name": row["name"],
                "prefix": row["prefix"],
            }
    return None


def _password_hash(password: str, salt: str) -> str:
    import hashlib

    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()


def _email_ok(email: str) -> bool:
    if len(email) < 5 or len(email) > 120 or any(ord(ch) < 32 for ch in email):
        return False
    local, sep, host = email.partition("@")
    return bool(sep) and "." in host and " " not in email and local and host


def create_account(name: str, email: str, password: str) -> dict[str, Any]:
    """Create a caller account and its API key. The key is returned only from this call."""
    import sqlite3

    clean_name = name.strip()
    clean_email = email.strip().lower()
    if not clean_name or len(clean_name) > 80 or any(ord(ch) < 32 for ch in clean_name):
        raise ValueError("name")
    if not _email_ok(clean_email):
        raise ValueError("email")
    if len(password) < 8 or len(password) > 200:
        raise ValueError("password")
    conn = connect()
    if conn.execute("SELECT 1 FROM accounts WHERE email = ?", (clean_email,)).fetchone():
        raise ValueError("exists")
    import secrets

    key = create_api_key(clean_name, role="user", owner_email=clean_email)
    salt = secrets.token_hex(16)
    now = time.time()
    try:
        with _lock:
            conn.execute(
                "INSERT INTO accounts(email, name, password_hash, salt, key_id, created_at) VALUES (?,?,?,?,?,?)",
                (clean_email, clean_name, _password_hash(password, salt), salt, key["key_id"], now),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        revoke_api_key(key["key_id"])
        raise ValueError("exists") from None
    return {
        "email": clean_email,
        "name": clean_name,
        "role": "user",
        "key_id": key["key_id"],
        "prefix": key["prefix"],
        "token": key["token"],
    }


def login_account(email: str, password: str) -> dict[str, Any] | None:
    """Check email and password. Returns a session token for the same caller key."""
    import hmac
    import secrets

    clean_email = email.strip().lower()
    if not clean_email or not password:
        return None
    conn = connect()
    row = conn.execute(
        "SELECT name, password_hash, salt, key_id FROM accounts WHERE email = ?",
        (clean_email,),
    ).fetchone()
    if row is None:
        return None
    digest = _password_hash(password, str(row["salt"]))
    if not hmac.compare_digest(digest, str(row["password_hash"])):
        return None
    key = conn.execute(
        "SELECT role, prefix, revoked FROM api_keys WHERE key_id = ?",
        (row["key_id"],),
    ).fetchone()
    if key is None or key["revoked"]:
        return None
    token = "ps_" + secrets.token_urlsafe(32)
    with _lock:
        conn.execute(
            "INSERT INTO sessions(token_hash, key_id, created_at, revoked) VALUES (?,?,?,0)",
            (hash_token(token), row["key_id"], time.time()),
        )
        conn.commit()
    return {
        "email": clean_email,
        "name": row["name"],
        "role": key["role"],
        "key_id": row["key_id"],
        "prefix": key["prefix"],
        "token": token,
    }
