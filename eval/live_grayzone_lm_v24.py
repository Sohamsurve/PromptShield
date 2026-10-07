#!/usr/bin/env python3
"""Live gray-zone subset on length-matched pool (SEED=42). Hash in FREEZE before run.

Uses JUDGE_GRAY_ZONE_ONLY=1. Never tunes. Writes eval/reports/live_grayzone_lm_v24.json.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT))

os.environ.setdefault("PROMPTSHIELD_POLICY", "template")
os.environ["JUDGE_GRAY_ZONE_ONLY"] = "1"
os.environ.pop("JUDGE_DISABLE", None)
os.environ.pop("JUDGE_CASCADE", None)


def _load(path: Path, n: int) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
        if len(rows) >= n:
            break
    return rows


def main() -> int:
    from promptshield.domain import ScanRequest, SourceType, TrustLevel
    from promptshield.pipeline import scan

    atk = _load(ROOT / "eval/data/length_matched/attacks.jsonl", 20)
    neg = _load(ROOT / "eval/data/length_matched/benign.jsonl", 20)
    acted = {"sanitize", "quarantine", "block", "escalate"}
    judge_calls = 0
    atk_hit = 0
    neg_hit = 0
    for row in atk:
        text = row.get("text") or row.get("content") or ""
        r = scan(ScanRequest(source_type=SourceType.text, content=text, trust=TrustLevel.T3), noop=False)
        if r.decision.value in acted:
            atk_hit += 1
        if any("judge" in d for d in (r.degraded or [])) or any(
            getattr(f, "detector", "") == "judge" for f in (r.findings or [])
        ):
            judge_calls += 1
        # telemetry: count judge findings
        for f in r.findings or []:
            if getattr(f, "detector", None) == "judge":
                judge_calls += 1
                break
    for row in neg:
        text = row.get("text") or row.get("content") or ""
        r = scan(ScanRequest(source_type=SourceType.text, content=text, trust=TrustLevel.T3), noop=False)
        if r.decision.value in acted:
            neg_hit += 1
        for f in r.findings or []:
            if getattr(f, "detector", None) == "judge":
                judge_calls += 1
                break

    out = {
        "seed": SEED,
        "mode": "gray_zone_only",
        "n_atk": len(atk),
        "n_neg": len(neg),
        "acted_atk": atk_hit,
        "acted_neg": neg_hit,
        "acted_recall": atk_hit / len(atk) if atk else None,
        "acted_fpr": neg_hit / len(neg) if neg else None,
        "judge_calls": judge_calls,
        "note": "LM subset only; not independent; no tuning",
    }
    dest = ROOT / "eval/reports/live_grayzone_lm_v24.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
