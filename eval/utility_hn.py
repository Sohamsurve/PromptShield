#!/usr/bin/env python3
"""Utility on >=30 benign tasks that include hard-negative-like content."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from promptshield.agent.aria import run_content  # noqa: E402
from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402


def main() -> dict:
    path = ROOT / "eval" / "data" / "utility" / "hn_like_benign.jsonl"
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    decisions: Counter[str] = Counter()
    off_ok = on_ok = 0
    for r in rows:
        scan_res = scan(
            ScanRequest(source_type=SourceType.text, content=r["content"], trust=TrustLevel.T1),
            noop=False,
        )
        decisions[scan_res.decision.value] += 1
        off = run_content(r["content"], firewall=False, expect_benign=True, user_goal=r.get("goal", "Summarise"))
        on = run_content(r["content"], firewall=True, expect_benign=True, user_goal=r.get("goal", "Summarise"))
        off_ok += int(off["outcome"]["task_completed"])
        on_ok += int(on["outcome"]["task_completed"])
    n = len(rows)
    utility = rate(on_ok, off_ok) if off_ok else None
    payload = {
        "n": n,
        "utility": utility,
        "utility_on_ok": on_ok,
        "utility_off_ok": off_ok,
        "utility_ci_on_completion": list(wilson_ci(on_ok, n)),
        "decision_breakdown": dict(decisions),
        "allow_rate": rate(decisions.get("allow", 0), n),
        "allow_ci": list(wilson_ci(decisions.get("allow", 0), n)),
    }
    out = ROOT / "eval" / "reports" / "utility_hn.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return payload


if __name__ == "__main__":
    main()
