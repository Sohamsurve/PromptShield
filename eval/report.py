"""Write eval reports to eval/reports/<timestamp>/."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_report(root: Path, payload: dict[str, Any]) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = root / "eval" / "reports" / ts
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out / "heatmap.json").write_text(json.dumps(payload.get("heatmap", {}), indent=2), encoding="utf-8")
    md = _to_markdown(payload)
    (out / "report.md").write_text(md, encoding="utf-8")
    latest = root / "eval" / "reports" / "latest"
    if latest.exists() or latest.is_symlink():
        if latest.is_symlink() or latest.is_file():
            latest.unlink()
        else:
            # directory from prior run
            import shutil

            shutil.rmtree(latest)
    try:
        latest.symlink_to(out, target_is_directory=True)
    except OSError:
        (latest).mkdir(parents=True, exist_ok=True)
        (latest / "report.json").write_text((out / "report.json").read_text(encoding="utf-8"), encoding="utf-8")
    return out


def _to_markdown(payload: dict[str, Any]) -> str:
    asr_off = payload.get("asr_off", {})
    asr_on = payload.get("asr_on", {})
    lines = [
        "# PromptShield evaluation report",
        "",
        f"- Mode: `{payload.get('mode')}`",
        f"- Attack fixtures: {payload.get('n_attack')}",
        f"- Benign fixtures: {payload.get('n_benign')}",
        f"- ASR(off): {asr_off.get('rate')} (n={asr_off.get('n')}, ci={asr_off.get('ci')})",
        f"- ASR(on): {asr_on.get('rate')} (n={asr_on.get('n')}, ci={asr_on.get('ci')})",
        f"- Thresholds passed: {payload.get('passed')}",
        "",
        "## Notes",
        payload.get("notes", ""),
        "",
    ]
    return "\n".join(lines)
