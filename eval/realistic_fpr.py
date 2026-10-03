#!/usr/bin/env python3
"""First-run FPR on realistic benign + hard-negative sets (after FREEZE hash)."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT))

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def eval_set(rows: list[dict]) -> dict:
    fp = 0
    by_cat: dict[str, Counter] = defaultdict(Counter)
    by_decision: Counter = Counter()
    for r in rows:
        st = r.get("source_type") or "text"
        try:
            source = SourceType(st)
        except Exception:
            source = SourceType.text
        res = scan(
            ScanRequest(source_type=source, content=r["content"], trust=TrustLevel.T1),
            noop=False,
        )
        by_decision[res.decision.value] += 1
        cat = r.get("category") or "other"
        by_cat[cat][res.decision.value] += 1
        if res.decision != Decision.allow:
            fp += 1
            by_cat[cat]["fp"] += 1
        by_cat[cat]["n"] += 1
    n = len(rows)
    cat_out = {}
    for cat, c in by_cat.items():
        n_c = c["n"]
        fp_c = c["fp"]
        cat_out[cat] = {
            "n": n_c,
            "fp": fp_c,
            "fpr": rate(fp_c, n_c),
            "ci": list(wilson_ci(fp_c, n_c)),
            "decisions": {k: v for k, v in c.items() if k not in {"n", "fp"}},
        }
    return {
        "n": n,
        "fp": fp,
        "fpr": rate(fp, n),
        "ci": list(wilson_ci(fp, n)),
        "by_decision": dict(by_decision),
        "by_category": cat_out,
    }


def main() -> dict:
    benign = _load(ROOT / "eval" / "data" / "realistic" / "benign.jsonl")
    hn = _load(ROOT / "eval" / "data" / "realistic" / "hard_negatives.jsonl")
    payload = {"benign": eval_set(benign), "hard_negative": eval_set(hn)}
    out = ROOT / "eval" / "reports" / "realistic_fpr_v11.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2)[:4000])
    print(f"Wrote {out}")
    return payload


if __name__ == "__main__":
    main()
