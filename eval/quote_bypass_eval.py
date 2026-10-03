#!/usr/bin/env python3
"""Evaluate quotation-bypass sets at T2/T3 — risk must stay >= sanitize/block floor."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT))

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def eval_rows(rows: list[dict], trust: TrustLevel) -> dict:
    # sanitize/block = not allow (and preferably risk high)
    hits = 0
    details = []
    for r in rows:
        res = scan(
            ScanRequest(
                source_type=SourceType.text,
                content=r["content"],
                trust=trust,
            ),
            noop=False,
        )
        ok = res.decision in {Decision.block, Decision.sanitize, Decision.quarantine}
        # Also require risk not collapsed below sanitize band (~0.6)
        ok = ok and res.risk >= 0.6
        hits += int(ok)
        details.append(
            {
                "id": r["id"],
                "decision": res.decision.value,
                "risk": res.risk,
                "ok": ok,
            }
        )
    n = len(rows)
    return {
        "n": n,
        "pass_rate": rate(hits, n),
        "ci": list(wilson_ci(hits, n)),
        "passed": hits,
        "details": details,
    }


def main() -> dict:
    dev = _load(ROOT / "eval" / "data" / "quote_bypass" / "dev.jsonl")
    sealed = _load(ROOT / "eval" / "data" / "sealed" / "quote_bypass_v11.jsonl")
    payload = {
        "dev_T3": {k: v for k, v in eval_rows(dev, TrustLevel.T3).items() if k != "details"},
        "dev_T2": {k: v for k, v in eval_rows(dev, TrustLevel.T2).items() if k != "details"},
        "sealed_T3": {k: v for k, v in eval_rows(sealed, TrustLevel.T3).items() if k != "details"},
        "sealed_T2": {k: v for k, v in eval_rows(sealed, TrustLevel.T2).items() if k != "details"},
        "dev_T3_full": eval_rows(dev, TrustLevel.T3),
        "sealed_T3_full": eval_rows(sealed, TrustLevel.T3),
    }
    out = ROOT / "eval" / "reports" / "quote_bypass_v11.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in payload if "full" not in k}, indent=2))
    return payload


if __name__ == "__main__":
    main()
