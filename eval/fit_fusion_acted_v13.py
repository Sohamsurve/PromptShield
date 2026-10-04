#!/usr/bin/env python3
"""Decision-level fusion + clf_graded fit on train+dev only (v1.3 Part B).

Operating point (pre-registered in FREEZE): maximise ACTED on attacks subject to
dev benign+HN ACTED FPR <= 2%.

Uses full pipeline.scan so quotation dampening / signature floor match product.
Never reads sealed / redteam staging sets.
SEED=42.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT))

SEED = 42
POLICY_PATH = ROOT / "apps/api/src/promptshield/policies/default.yml"

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.detect.classifier import reset_classifier_cache  # noqa: E402
from promptshield import pipeline as pipe  # noqa: E402

ACTED = {Decision.sanitize, Decision.quarantine, Decision.block, Decision.escalate}


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _rows_split(path: Path, splits: set[str], label: str | None = None) -> list[dict]:
    out = []
    for r in _load(path):
        if r.get("split") not in splits:
            continue
        if label and r.get("label") != label:
            continue
        out.append(r)
    return out


def _scan(text: str, source_type: str, session_id: str):
    try:
        st = SourceType(source_type)
    except Exception:
        st = SourceType.text
    trust = TrustLevel.T1 if st in {SourceType.text, SourceType.user_message} else TrustLevel.T3
    return pipe.scan(
        ScanRequest(source_type=st, content=text, trust=trust, session_id=session_id),
        noop=False,
    )


def eval_sets(atk: list[dict], neg: list[dict], tag: str) -> tuple[float, float, int, int]:
    acted = 0
    for i, r in enumerate(atk):
        res = _scan(r.get("content") or "", r.get("source_type") or "text", f"{tag}_a_{i}")
        acted += int(res.decision in ACTED)
    fp = 0
    for i, r in enumerate(neg):
        res = _scan(r.get("content") or "", r.get("source_type") or "text", f"{tag}_n_{i}")
        fp += int(res.decision in ACTED)
    ar = acted / max(1, len(atk))
    fpr = fp / max(1, len(neg))
    return ar, fpr, acted, fp


def apply_policy(fusion: dict, graded: dict) -> dict:
    """Write fusion + clf_graded only — do not loosen per-source sanitize_span."""
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8")) or {}
    policy["fusion"] = fusion
    policy["clf_graded"] = graded
    POLICY_PATH.write_text(yaml.safe_dump(policy, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return policy


def main() -> None:
    random.seed(SEED)
    reset_classifier_cache()
    splits = {"train", "dev"}
    attacks = [
        r
        for r in _rows_split(ROOT / "eval/data/attacks/synth_text.jsonl", splits, "attack")
        if (r.get("source_type") or "text") in {"text", "user_message", "markdown"}
    ]
    benign = _rows_split(ROOT / "eval/data/benign/synth.jsonl", splits, "benign")
    hn = _rows_split(ROOT / "eval/data/hard_negatives/synth.jsonl", splits, "hard_negative")
    dev_ben = [r for r in _load(ROOT / "eval/data/realistic_dev/benign.jsonl") if r.get("split") == "dev"]
    dev_hn = [
        r for r in _load(ROOT / "eval/data/realistic_dev/hard_negatives.jsonl") if r.get("split") == "dev"
    ]

    dev_atk = [r for r in attacks if r.get("split") == "dev"]
    random.shuffle(dev_atk)
    dev_atk = dev_atk[:80]
    neg = [r for r in benign if r.get("split") == "dev"] + [
        r for r in hn if r.get("split") == "dev"
    ]
    # subsample realistic_dev into operating-point neg set
    random.shuffle(dev_ben)
    random.shuffle(dev_hn)
    neg = neg + dev_ben[:120] + dev_hn[:80]
    random.shuffle(neg)
    neg = neg[:220]

    print(f"dev_atk={len(dev_atk)} neg={len(neg)}", flush=True)

    base = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8")) or {}
    base_fusion = dict(base.get("fusion") or {})

    grid = []
    for w_ml in [3.5, 5.0, 7.0]:
        for b in [-6.5, -5.1, -4.0]:
            for clf_s, clf_q, clf_b in [
                (0.85, 0.92, 0.98),
                (0.90, 0.95, 0.99),
                (0.78, 0.88, 0.96),
            ]:
                fusion = {
                    **base_fusion,
                    "b": b,
                    "w_ml": w_ml,
                    "w_sig": float(base_fusion.get("w_sig", 6.7)),
                    "w_h": float(base_fusion.get("w_h", 1.5)),
                    "w_j": float(base_fusion.get("w_j", 2.0)),
                    "w_hid": float(base_fusion.get("w_hid", 0.23)),
                    "w_enc": float(base_fusion.get("w_enc", 0.03)),
                    "w_trust": base_fusion.get("w_trust")
                    or {"T0": -2.0, "T1": 0.0, "T2": 0.4, "T3": 0.6},
                    "w_sess": float(base_fusion.get("w_sess", 1.5)),
                }
                graded = {"sanitize": clf_s, "quarantine": clf_q, "block": clf_b}
                grid.append((fusion, graded))

    grid.insert(0, (base_fusion, {"sanitize": 0.85, "quarantine": 0.92, "block": 0.98}))

    curve = []
    best = None
    for i, (fusion, graded) in enumerate(grid):
        apply_policy(fusion, graded)
        ar, fpr, an, fn = eval_sets(dev_atk, neg, tag=f"g{i}")
        row = {
            "dev_acted": ar,
            "dev_fpr": fpr,
            "dev_acted_n": an,
            "dev_fp_n": fn,
            "w_ml": fusion.get("w_ml"),
            "b": fusion.get("b"),
            "graded": graded,
        }
        curve.append(row)
        print(f"[{i+1}/{len(grid)}] ACTED={ar:.3f} FPR={fpr:.3f} graded={graded}", flush=True)
        if fpr <= 0.02 + 1e-12:
            if best is None or ar > best[0]:
                best = (ar, fpr, fusion, graded)

    if best is None:
        min_fpr = min(c["dev_fpr"] for c in curve)
        pool = [c for c in curve if abs(c["dev_fpr"] - min_fpr) < 1e-12]
        pick = max(pool, key=lambda c: c["dev_acted"])
        # recover fusion from pick fields — re-find in grid
        for fusion, graded in grid:
            if fusion.get("w_ml") == pick["w_ml"] and fusion.get("b") == pick["b"] and graded == pick["graded"]:
                best = (pick["dev_acted"], pick["dev_fpr"], fusion, graded)
                break
        note = f"no point met FPR<=2% (min_fpr={min_fpr:.4f}); chose min-FPR max-ACTED"
    else:
        note = "operating point met FPR<=2% on dev"

    assert best is not None
    ar, fpr, fusion, graded = best
    policy = apply_policy(fusion, graded)
    policy["version"] = int(policy.get("version", 1)) + 1
    POLICY_PATH.write_text(yaml.safe_dump(policy, sort_keys=False, allow_unicode=True), encoding="utf-8")

    # Final verify
    ar2, fpr2, an2, fn2 = eval_sets(dev_atk, neg, tag="final")
    report = {
        "seed": SEED,
        "note": note,
        "chosen": {
            "dev_acted": ar2,
            "dev_fpr": fpr2,
            "dev_acted_n": an2,
            "dev_fp_n": fn2,
            "fusion": fusion,
            "clf_graded": graded,
        },
        "curve": sorted(curve, key=lambda x: (-x["dev_acted"], x["dev_fpr"]))[:30],
        "n_dev_atk": len(dev_atk),
        "n_neg": len(neg),
        "judge": "not run" if not __import__("os").getenv("LLM_API_KEY") else "pending",
    }
    out = ROOT / "eval/reports/fit_fusion_acted_v13.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["chosen"], indent=2))
    print(f"Wrote {POLICY_PATH} and {out}")


if __name__ == "__main__":
    main()
