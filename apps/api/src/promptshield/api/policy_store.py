"""Durable policy versions on disk (demo-local; no DB required).

Never mutates the sealed template `policies/default.yml`. Writes go to
`apps/api/data/active_policy.yml` plus versioned snapshots under
`apps/api/data/policy_history/`.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

_REPO = Path(__file__).resolve().parents[5]
_DEFAULT = _REPO / "apps" / "api" / "src" / "promptshield" / "policies" / "default.yml"
_DATA = _REPO / "apps" / "api" / "data"
_ACTIVE = _DATA / "active_policy.yml"
_HISTORY = _DATA / "policy_history"


def default_policy_path() -> Path:
    return _DEFAULT


def active_policy_path() -> Path:
    return _ACTIVE


def resolve_policy_path() -> Path:
    """Active override if present, else sealed default template."""
    return _ACTIVE if _ACTIVE.exists() else _DEFAULT


def _ensure() -> None:
    _DATA.mkdir(parents=True, exist_ok=True)
    _HISTORY.mkdir(parents=True, exist_ok=True)


def current_policy() -> dict[str, Any]:
    path = resolve_policy_path()
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def list_versions() -> list[dict[str, Any]]:
    _ensure()
    items = []
    for p in sorted(_HISTORY.glob("v*.json"), reverse=True):
        meta = json.loads(p.read_text(encoding="utf-8"))
        items.append(
            {
                "version": meta.get("version"),
                "ts": meta.get("ts"),
                "note": meta.get("note", ""),
                "path": str(p.relative_to(_REPO)),
            }
        )
    return items


def save_policy(body: dict[str, Any], *, note: str = "") -> dict[str, Any]:
    """Write active policy YAML and append a versioned snapshot. Never touches default.yml."""
    _ensure()
    if not _ACTIVE.exists():
        shutil.copyfile(_DEFAULT, _ACTIVE)
    cur = current_policy()
    version = int(cur.get("version") or 1) + 1
    body = dict(body)
    # Strip UI-only keys
    body.pop("_versions", None)
    body.pop("note", None)
    body["version"] = version
    _ACTIVE.write_text(yaml.safe_dump(body, sort_keys=False, allow_unicode=True), encoding="utf-8")
    snap = {
        "version": version,
        "ts": datetime.now(timezone.utc).isoformat(),
        "note": note,
        "policy": body,
    }
    out = _HISTORY / f"v{version:04d}.json"
    out.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return {"version": version, "ts": snap["ts"], "path": str(out.relative_to(_REPO))}


def get_version(version: int) -> dict[str, Any]:
    path = _HISTORY / f"v{version:04d}.json"
    if not path.exists():
        raise FileNotFoundError(f"policy version {version} not found")
    return json.loads(path.read_text(encoding="utf-8"))


def diff_versions(a: int, b: int) -> dict[str, Any]:
    pa = get_version(a)["policy"]
    pb = get_version(b)["policy"]
    keys = sorted(set(pa) | set(pb))
    changed = []
    for k in keys:
        if pa.get(k) != pb.get(k):
            changed.append({"key": k, "from": pa.get(k), "to": pb.get(k)})
    return {"a": a, "b": b, "changed": changed}
