"""Durable policy versions on disk (demo-local; no DB required).

Never mutates the sealed template `policies/default.yml`. Writes go to
`apps/api/data/active_policy.yml` plus versioned snapshots under
`apps/api/data/policy_history/`.

Isolation: set ``PROMPTSHIELD_POLICY_DIR`` to a temp directory for tests /
conformance / accept so the developer's active policy is never touched.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

_REPO = Path(__file__).resolve().parents[5]
_DEFAULT = _REPO / "apps" / "api" / "src" / "promptshield" / "policies" / "default.yml"


def _data_dir() -> Path:
    override = (os.getenv("PROMPTSHIELD_POLICY_DIR") or "").strip()
    if override:
        return Path(override)
    return _REPO / "apps" / "api" / "data"


def data_dir() -> Path:
    """Public data directory (policy + local queues). Honours PROMPTSHIELD_POLICY_DIR."""
    return _data_dir()


def _active_path() -> Path:
    return _data_dir() / "active_policy.yml"


def _history_dir() -> Path:
    return _data_dir() / "policy_history"


def default_policy_path() -> Path:
    return _DEFAULT


def active_policy_path() -> Path:
    return _active_path()


def resolve_policy_path() -> Path:
    """Active override if present, else sealed default template.

    Set ``PROMPTSHIELD_POLICY=template`` for eval harnesses that must not
    read demo ``active_policy.yml`` overrides.
    """
    mode = (os.getenv("PROMPTSHIELD_POLICY") or "").strip().lower()
    if mode in {"template", "default", "sealed"}:
        return _DEFAULT
    active = _active_path()
    return active if active.exists() else _DEFAULT


def _ensure() -> None:
    d = _data_dir()
    d.mkdir(parents=True, exist_ok=True)
    _history_dir().mkdir(parents=True, exist_ok=True)


def current_policy() -> dict[str, Any]:
    path = resolve_policy_path()
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def template_policy() -> dict[str, Any]:
    return yaml.safe_load(_DEFAULT.read_text(encoding="utf-8")) or {}


def policy_meta() -> dict[str, Any]:
    """Active version + whether it differs from the shipped template."""
    active_path = _active_path()
    using_active = active_path.exists() and (os.getenv("PROMPTSHIELD_POLICY") or "").strip().lower() not in {
        "template",
        "default",
        "sealed",
    }
    active = current_policy()
    template = template_policy()
    # Compare without version / demo notes that always drift
    def _norm(p: dict[str, Any]) -> dict[str, Any]:
        skip = {"version", "operating_point_note", "demo_config"}
        return {k: v for k, v in p.items() if k not in skip}

    differs = _norm(active) != _norm(template) if using_active else False
    return {
        "active_version": active.get("version"),
        "template_version": template.get("version"),
        "using_active_file": using_active,
        "differs_from_template": differs,
        "policy_dir": str(_data_dir()),
        "presets": {
            "balanced": {
                "label": "Balanced (shipped demo)",
                "dev_acted": 0.575,
                "dev_fpr": 0.106,
                "note": "dev curve-C measured under template; demo_config (no FPR≤2% fusion point)",
            },
            "low_false_alarms": {
                "label": "Low false alarms",
                "dev_acted": 0.25,
                "dev_fpr": 0.0156,
                "risk_threshold": 0.9,
                "note": "dev risk-sweep proxy at thr=0.9 (not fusion refit); marked DEV numbers",
            },
        },
    }


def list_versions() -> list[dict[str, Any]]:
    _ensure()
    items = []
    for p in sorted(_history_dir().glob("v*.json"), reverse=True):
        meta = json.loads(p.read_text(encoding="utf-8"))
        items.append(
            {
                "version": meta.get("version"),
                "ts": meta.get("ts"),
                "note": meta.get("note", ""),
                "path": str(p),
            }
        )
    return items


_MAX_BLOCK = 0.95


def _clamp_blocks(body: dict[str, Any]) -> dict[str, Any]:
    """A block threshold above 0.95 would let high-risk content through."""
    sources = body.get("sources")
    if isinstance(sources, dict):
        for cfg in sources.values():
            if isinstance(cfg, dict) and "block" in cfg:
                try:
                    cfg["block"] = min(float(cfg["block"]), _MAX_BLOCK)
                except (TypeError, ValueError):
                    cfg["block"] = _MAX_BLOCK
    graded = body.get("clf_graded")
    if isinstance(graded, dict) and "block" in graded:
        try:
            graded["block"] = min(float(graded["block"]), _MAX_BLOCK)
        except (TypeError, ValueError):
            graded["block"] = _MAX_BLOCK
    return body


def save_policy(body: dict[str, Any], *, note: str = "") -> dict[str, Any]:
    """Write active policy YAML and append a versioned snapshot. Never touches default.yml."""
    _ensure()
    active = _active_path()
    if not active.exists():
        shutil.copyfile(_DEFAULT, active)
    cur = yaml.safe_load(active.read_text(encoding="utf-8")) or {}
    version = int(cur.get("version") or 1) + 1
    body = dict(body)
    body.pop("_versions", None)
    body.pop("_meta", None)
    body.pop("note", None)
    body = _clamp_blocks(body)
    body["version"] = version
    active.write_text(yaml.safe_dump(body, sort_keys=False, allow_unicode=True), encoding="utf-8")
    snap = {
        "version": version,
        "ts": datetime.now(timezone.utc).isoformat(),
        "note": note,
        "policy": body,
    }
    out = _history_dir() / f"v{version:04d}.json"
    out.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return {"version": version, "ts": snap["ts"], "path": str(out)}


def reset_to_template(*, note: str = "reset to shipped template") -> dict[str, Any]:
    """Copy FREEZE-hashed default.yml over active_policy.yml and snapshot history."""
    _ensure()
    template = template_policy()
    body = dict(template)
    return save_policy(body, note=note)


def get_version(version: int) -> dict[str, Any]:
    path = _history_dir() / f"v{version:04d}.json"
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


def apply_preset(name: str) -> dict[str, Any]:
    """Apply Balanced or Low false alarms preset (dev-measured numbers)."""
    template = template_policy()
    body = dict(template)
    if name == "low_false_alarms":
        # Raise source action thresholds toward risk thr≈0.9 proxy
        sources = dict(body.get("sources") or {})
        for _k, cfg in list(sources.items()):
            if not isinstance(cfg, dict):
                continue
            c = dict(cfg)
            c["sanitize_span"] = 0.9
            c["quarantine"] = 0.92
            c["block"] = 0.95
            sources[_k] = c
        body["sources"] = sources
        body["operating_point_note"] = (
            "Low false alarms preset: DEV risk-sweep thr=0.9 → ACTED≈0.25 FPR≈0.0156 (not fusion refit)."
        )
        body["demo_config"] = True
        return save_policy(body, note="preset: low_false_alarms")
    # balanced = reset toward shipped template numbers
    body["operating_point_note"] = template.get("operating_point_note") or (
        "Balanced shipped demo; DEV curve-C ACTED≈0.575 FPR≈0.106"
    )
    return save_policy(body, note="preset: balanced")
