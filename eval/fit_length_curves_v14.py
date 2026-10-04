#!/usr/bin/env python3
"""Operating curves: before redteam / unmatched redteam / length-matched (SEED=42).

Reports ACTED vs benign+HN FPR on fixed evaluation slices. Refits clf_graded/fusion
grid WITHOUT unmatched dev_redteam for the length-matched claimed fit.
Also checks classifier features for length proxies.
Never reads independent staging.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

SEED = 42
POLICY_PATH = ROOT / "apps/api/src/promptshield/policies/default.yml"
OUT = ROOT / "eval/reports/fit_length_curves_v14.json"

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.detect.classifier import get_classifier, reset_classifier_cache  # noqa: E402
from promptshield import pipeline as pipe  # noqa: E402

ACTED = {Decision.sanitize, Decision.quarantine, Decision.block, Decision.escalate}


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _content(r: dict) -> str:
    c = r.get("content")
    if isinstance(c, list):
        return "\n".join(str(x) for x in c)
    return str(c or "")


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


def eval_sets(atk: list[dict], neg: list[dict], tag: str) -> dict:
    acted = 0
    for i, r in enumerate(atk):
        res = _scan(_content(r), r.get("source_type") or "text", f"{tag}_a_{i}")
        acted += int(res.decision in ACTED)
    fp = 0
    for i, r in enumerate(neg):
        res = _scan(_content(r), r.get("source_type") or "text", f"{tag}_n_{i}")
        fp += int(res.decision in ACTED)
    return {
        "n_atk": len(atk),
        "n_neg": len(neg),
        "acted_hits": acted,
        "fp_hits": fp,
        "ACTED": acted / max(1, len(atk)),
        "FPR": fp / max(1, len(neg)),
    }


def apply_policy(fusion: dict, graded: dict) -> None:
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8")) or {}
    policy["fusion"] = fusion
    policy["clf_graded"] = graded
    POLICY_PATH.write_text(yaml.safe_dump(policy, sort_keys=False, allow_unicode=True), encoding="utf-8")


def grid_search(atk: list[dict], neg: list[dict], tag: str) -> dict:
    base = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8")) or {}
    base_fusion = dict(base.get("fusion") or {})
    grid = []
    for w_ml in [3.5, 5.0838, 7.0]:
        for b in [-6.5, -5.1085, -4.0]:
            for graded in (
                {"sanitize": 0.85, "quarantine": 0.92, "block": 0.98},
                {"sanitize": 0.90, "quarantine": 0.95, "block": 0.99},
                {"sanitize": 0.78, "quarantine": 0.88, "block": 0.96},
            ):
                fusion = {**base_fusion, "b": b, "w_ml": w_ml}
                grid.append((fusion, graded))
    grid.insert(0, (base_fusion, {"sanitize": 0.85, "quarantine": 0.92, "block": 0.98}))

    curve = []
    best = None
    for i, (fusion, graded) in enumerate(grid):
        apply_policy(fusion, graded)
        m = eval_sets(atk, neg, tag=f"{tag}_g{i}")
        row = {
            "ACTED": m["ACTED"],
            "FPR": m["FPR"],
            "acted_hits": m["acted_hits"],
            "fp_hits": m["fp_hits"],
            "w_ml": fusion.get("w_ml"),
            "b": fusion.get("b"),
            "graded": graded,
        }
        curve.append(row)
        print(f"  [{tag} {i+1}/{len(grid)}] ACTED={m['ACTED']:.3f} FPR={m['FPR']:.3f}", flush=True)
        if m["FPR"] <= 0.02 + 1e-12:
            if best is None or m["ACTED"] > best["ACTED"]:
                best = {**row, "fusion": fusion}
    if best is None:
        min_fpr = min(c["FPR"] for c in curve)
        pool = [c for c in curve if abs(c["FPR"] - min_fpr) < 1e-12]
        pick = max(pool, key=lambda c: c["ACTED"])
        for fusion, graded in grid:
            if fusion.get("w_ml") == pick["w_ml"] and fusion.get("b") == pick["b"] and graded == pick["graded"]:
                best = {**pick, "fusion": fusion}
                break
        note = f"no point met FPR<=2% (min_fpr={min_fpr:.4f}); chose min-FPR max-ACTED"
    else:
        note = "operating point met FPR<=2%"
    assert best is not None
    apply_policy(best["fusion"], best["graded"])
    final = eval_sets(atk, neg, tag=f"{tag}_final")
    return {
        "note": note,
        "chosen": {
            "ACTED": final["ACTED"],
            "FPR": final["FPR"],
            "acted_hits": final["acted_hits"],
            "fp_hits": final["fp_hits"],
            "n_atk": final["n_atk"],
            "n_neg": final["n_neg"],
            "fusion": best["fusion"],
            "clf_graded": best["graded"],
        },
        "curve": sorted(curve, key=lambda x: (-x["ACTED"], x["FPR"]))[:20],
    }


def length_proxy_check(rows: list[dict]) -> dict:
    """Correlate classifier score with char length; flag digit/len-like vocab tokens."""
    reset_classifier_cache()
    clf = get_classifier()
    pairs = []
    for r in rows:
        t = _content(r)
        if not t.strip():
            continue
        p = float(clf.predict_proba(t))
        pairs.append((len(t), p, r.get("label")))
    if len(pairs) < 10:
        return {"n": len(pairs)}
    # Pearson corr(len, score)
    xs = [a for a, _, _ in pairs]
    ys = [b for _, b, _ in pairs]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))
    corr = num / (denx * deny) if denx and deny else 0.0
    # Vocab tokens that look like length proxies
    vocab = getattr(clf, "vocabulary", None) or {}
    suspicious = []
    for tok in vocab:
        tl = str(tok).lower()
        if any(k in tl for k in ("len", "length", "chars", "words", "bytes", "token")):
            suspicious.append(tok)
        if tl.isdigit() and len(tl) <= 2:
            suspicious.append(tok)
    return {
        "n": len(pairs),
        "pearson_len_vs_clf": round(corr, 4),
        "suspicious_vocab_sample": suspicious[:30],
        "n_suspicious_vocab": len(suspicious),
        "note": "TF-IDF bag-of-words has no explicit length feature; high |corr| implies indirect length proxy via content.",
    }


def main() -> None:
    random.seed(SEED)
    reset_classifier_cache()

    synth_atk = [
        r
        for r in _rows_split(ROOT / "eval/data/attacks/synth_text.jsonl", {"dev"}, "attack")
        if (r.get("source_type") or "text") in {"text", "user_message", "markdown"}
    ]
    synth_ben = _rows_split(ROOT / "eval/data/benign/synth.jsonl", {"dev"}, "benign")
    synth_hn = _rows_split(ROOT / "eval/data/hard_negatives/synth.jsonl", {"dev"}, "hard_negative")
    real_ben = [r for r in _load(ROOT / "eval/data/realistic_dev/benign.jsonl") if r.get("split") == "dev"]
    real_hn = [r for r in _load(ROOT / "eval/data/realistic_dev/hard_negatives.jsonl") if r.get("split") == "dev"]

    rt_atk = _load(ROOT / "eval/data/dev_redteam/batch_a_attacks.jsonl")
    rt_hn = _load(ROOT / "eval/data/dev_redteam/batch_b_hard_negatives.jsonl")
    rt_ben = _load(ROOT / "eval/data/dev_redteam/batch_c_benign.jsonl")

    lm_atk = _load(ROOT / "eval/data/length_matched/attacks.jsonl")
    lm_ben = _load(ROOT / "eval/data/length_matched/benign.jsonl")
    lm_hn = _load(ROOT / "eval/data/length_matched/hard_negatives.jsonl")
    lm_long = _load(ROOT / "eval/data/length_matched/long_benign.jsonl")

    # Fixed eval slice sizes for fair curve comparison
    random.shuffle(synth_atk)
    base_atk = synth_atk[:80]
    base_neg = synth_ben[:60] + synth_hn[:40] + real_ben[:80] + real_hn[:40]
    random.shuffle(base_neg)
    base_neg = base_neg[:220]

    print("A) before dev_redteam", flush=True)
    cond_a = grid_search(base_atk, base_neg, tag="A")

    print("B) + unmatched dev_redteam", flush=True)
    atk_b = base_atk + rt_atk
    random.shuffle(atk_b)
    atk_b = atk_b[:120]
    neg_b = base_neg + rt_ben + rt_hn
    random.shuffle(neg_b)
    neg_b = neg_b[:320]
    cond_b = grid_search(atk_b, neg_b, tag="B")

    print("C) + length-matched (no unmatched redteam)", flush=True)
    atk_c = base_atk + lm_atk
    random.shuffle(atk_c)
    atk_c = atk_c[:120]
    neg_c = base_neg + lm_ben[:120] + lm_hn[:80] + lm_long[:40]
    random.shuffle(neg_c)
    neg_c = neg_c[:320]
    cond_c = grid_search(atk_c, neg_c, tag="C")

    # Claimed fit = C (length-matched, no unmatched redteam)
    apply_policy(cond_c["chosen"]["fusion"], cond_c["chosen"]["clf_graded"])
    policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8")) or {}
    policy["version"] = int(policy.get("version", 1)) + 1
    POLICY_PATH.write_text(yaml.safe_dump(policy, sort_keys=False, allow_unicode=True), encoding="utf-8")

    proxy = length_proxy_check(atk_c[:60] + neg_c[:60])

    report = {
        "seed": SEED,
        "v13_baseline_context": {
            "ACTED": 0.417,
            "FPR": 0.0938,
            "n_atk": 120,
            "n_neg": 320,
            "set": "synth_dev + unmatched_dev_redteam attacks; synth_dev+unmatched_redteam+realistic_dev neg",
        },
        "A_before_dev_redteam": cond_a,
        "B_unmatched_dev_redteam": cond_b,
        "C_length_matched": cond_c,
        "claimed_fit": "C_length_matched",
        "length_proxy_check": proxy,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "A": cond_a["chosen"],
        "B": cond_b["chosen"],
        "C": cond_c["chosen"],
        "proxy": proxy,
    }, indent=2, default=str))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
