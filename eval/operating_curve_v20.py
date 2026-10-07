#!/usr/bin/env python3
"""Full dev decision-level curve: ACTED vs benign+HN FPR (SEED=42).

Uses length-matched claimed-fit pool (curve C). Does not tune. Prints whether
any point reaches FPR≤2%. Hash in FREEZE before run.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT / "eval"))

SEED = 42
OUT = ROOT / "eval/reports/operating_curve_v20.json"

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield import pipeline as pipe  # noqa: E402
from promptshield.detect.classifier import get_classifier, reset_classifier_cache  # noqa: E402

ACTED = {Decision.sanitize, Decision.quarantine, Decision.block, Decision.escalate}


def _load(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _content(r: dict) -> str:
    c = r.get("content")
    return "\n".join(str(x) for x in c) if isinstance(c, list) else str(c or "")


def _scan(text: str, st: str, sid: str):
    try:
        source = SourceType(st)
    except Exception:
        source = SourceType.text
    trust = TrustLevel.T1 if source in {SourceType.text, SourceType.user_message} else TrustLevel.T3
    return pipe.scan(ScanRequest(source_type=source, content=text, trust=trust, session_id=sid), noop=False)


def main() -> None:
    os.environ["PROMPTSHIELD_POLICY"] = "template"
    os.environ.pop("JUDGE_DISABLE", None)
    os.environ["JUDGE_FORCE_OFFLINE"] = "1"
    reset_classifier_cache()
    get_classifier()
    from pools.curve_c_v14 import build_curve_c_pool  # noqa: E402

    atk, neg = build_curve_c_pool(ROOT, seed=SEED)
    lm_only_atk = _load(ROOT / "eval/data/length_matched/attacks.jsonl")[:120]
    lm_only_neg = (
        _load(ROOT / "eval/data/length_matched/benign.jsonl")[:160]
        + _load(ROOT / "eval/data/length_matched/hard_negatives.jsonl")[:160]
    )
    # Score each example once; sweep decision by risk threshold proxy via clf_graded isn't
    # exposed post-hoc — record risk and whether ACTED under shipped policy, plus risk sweep.
    rows_a, rows_n = [], []
    for i, r in enumerate(atk):
        res = _scan(_content(r), r.get("source_type") or "text", f"oc_a_{i}")
        rows_a.append({"risk": res.risk, "acted": res.decision in ACTED, "decision": res.decision.value})
    for i, r in enumerate(neg):
        res = _scan(_content(r), r.get("source_type") or "text", f"oc_n_{i}")
        rows_n.append({"risk": res.risk, "acted": res.decision in ACTED, "decision": res.decision.value})

    shipped_acted = sum(1 for r in rows_a if r["acted"]) / max(1, len(rows_a))
    shipped_fpr = sum(1 for r in rows_n if r["acted"]) / max(1, len(rows_n))

    curve = []
    for thr in [i / 100 for i in range(5, 96, 5)]:
        acted = sum(1 for r in rows_a if r["risk"] >= thr) / max(1, len(rows_a))
        fpr = sum(1 for r in rows_n if r["risk"] >= thr) / max(1, len(rows_n))
        curve.append({"risk_threshold": thr, "acted": round(acted, 4), "fpr": round(fpr, 4)})

    meets = [c for c in curve if c["fpr"] <= 0.02]
    best = max(meets, key=lambda c: c["acted"]) if meets else None

    # Legacy LM-only slice (documented mismatch vs fit C)
    rows_lm_a, rows_lm_n = [], []
    for i, r in enumerate(lm_only_atk):
        res = _scan(_content(r), r.get("source_type") or "text", f"lm_a_{i}")
        rows_lm_a.append({"acted": res.decision in ACTED})
    for i, r in enumerate(lm_only_neg):
        res = _scan(_content(r), r.get("source_type") or "text", f"lm_n_{i}")
        rows_lm_n.append({"acted": res.decision in ACTED})

    out = {
        "seed": SEED,
        "pool": "curve_C_v14",
        "n_atk": len(rows_a),
        "n_neg": len(rows_n),
        "shipped_policy": {"acted": round(shipped_acted, 4), "fpr": round(shipped_fpr, 4)},
        "legacy_lm_only_slice": {
            "n_atk": len(rows_lm_a),
            "n_neg": len(rows_lm_n),
            "acted": round(sum(1 for r in rows_lm_a if r["acted"]) / max(1, len(rows_lm_a)), 4),
            "fpr": round(sum(1 for r in rows_lm_n if r["acted"]) / max(1, len(rows_lm_n)), 4),
        },
        "risk_sweep": curve,
        "any_point_fpr_le_2pct": bool(meets),
        "best_under_2pct": best,
        "note": "Uses PROMPTSHIELD_POLICY=template and curve-C pool (fit_length_curves_v14). LM-only slice kept for regression audit.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
