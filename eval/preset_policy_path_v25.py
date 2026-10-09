"""Measure Balanced and Low-false-alarm presets through policy_store + scan.

Dev length-matched slice only. Unique session_id per item. No tuning.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

os.environ["JUDGE_FORCE_OFFLINE"] = "1"
os.environ.pop("CLASSIFIER_PATH", None)
os.environ.pop("PROMPTSHIELD_POLICY", None)


def _load(path: Path, n: int) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
        if len(rows) >= n:
            break
    return rows


def _measure(name: str, atk: list[dict], neg: list[dict]) -> dict:
    from promptshield.api import policy_store
    from promptshield.domain import ScanRequest, SourceType, TrustLevel
    from promptshield.pipeline import scan

    policy_store.apply_preset("low_false_alarms" if name == "low_false_alarms" else "balanced")
    acted = {"sanitize", "quarantine", "block", "escalate"}
    hit_a = hit_n = 0
    for i, row in enumerate(atk):
        text = row.get("text") or row.get("content") or ""
        r = scan(
            ScanRequest(
                source_type=SourceType.text,
                content=text,
                trust=TrustLevel.T3,
                session_id=f"pre25-{name}-atk-{i}",
            ),
            noop=False,
        )
        hit_a += r.decision.value in acted
    for i, row in enumerate(neg):
        text = row.get("text") or row.get("content") or ""
        r = scan(
            ScanRequest(
                source_type=SourceType.text,
                content=text,
                trust=TrustLevel.T3,
                session_id=f"pre25-{name}-neg-{i}",
            ),
            noop=False,
        )
        hit_n += r.decision.value in acted
    return {
        "preset": name,
        "n_atk": len(atk),
        "n_neg": len(neg),
        "acted_recall": hit_a / len(atk),
        "acted_fpr": hit_n / len(neg),
        "judge": "offline",
    }


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="ps-preset-")
    os.environ["PROMPTSHIELD_POLICY_DIR"] = tmp
    atk = _load(ROOT / "eval/data/length_matched/attacks.jsonl", 20)
    neg = _load(ROOT / "eval/data/length_matched/benign.jsonl", 20)
    out = {
        "balanced": _measure("balanced", atk, neg),
        "low_false_alarms": _measure("low_false_alarms", atk, neg),
        "note": "length-matched dev slice n=20/20; not independent; no tuning",
    }
    dest = ROOT / "eval/reports/preset_policy_path_v25.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
