#!/usr/bin/env python3
"""Regression report: curve A/B/C pools vs shipped template policy (SEED=42).

Explains operating_curve_v20 mismatch (LM-only slice). FP breakdown by detector/rule.
Cascade gating rates on synth dev. Hash in FREEZE before run.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT / "eval"))

SEED = 42
OUT = ROOT / "eval/reports/regression_policy_v23.json"
POLICY_TEMPLATE = ROOT / "apps/api/src/promptshield/policies/default.yml"

from pools.curve_c_v14 import build_curve_c_pool  # noqa: E402
from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield import pipeline as pipe  # noqa: E402
from promptshield.detect.classifier import reset_classifier_cache  # noqa: E402
from promptshield import scan_telemetry  # noqa: E402

ACTED = {Decision.sanitize, Decision.quarantine, Decision.block, Decision.escalate}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


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


def _metrics(atk: list[dict], neg: list[dict], tag: str) -> dict:
    acted = fp = 0
    fp_rules: Counter[str] = Counter()
    fp_layers: Counter[str] = Counter()
    for i, r in enumerate(atk):
        res = _scan(_content(r), r.get("source_type") or "text", f"{tag}_a_{i}")
        acted += int(res.decision in ACTED)
    for i, r in enumerate(neg):
        res = _scan(_content(r), r.get("source_type") or "text", f"{tag}_n_{i}")
        if res.decision in ACTED:
            fp += 1
            for f in res.findings:
                fp_layers[f.detector or "unknown"] += 1
                key = f.rule_id or f.reason_code or f.detector or "unknown"
                fp_rules[key] += 1
    return {
        "n_atk": len(atk),
        "n_neg": len(neg),
        "ACTED": round(acted / max(1, len(atk)), 4),
        "FPR": round(fp / max(1, len(neg)), 4),
        "fp_by_layer": dict(fp_layers.most_common(20)),
        "fp_by_rule": dict(fp_rules.most_common(30)),
    }


def _build_pools() -> dict:
    random.seed(SEED)
    from pools.curve_c_v14 import _rows_split, _load as pool_load  # noqa: E402

    synth_atk = [
        r
        for r in _rows_split(ROOT / "eval/data/attacks/synth_text.jsonl", {"dev"}, "attack")
        if (r.get("source_type") or "text") in {"text", "user_message", "markdown"}
    ]
    synth_ben = _rows_split(ROOT / "eval/data/benign/synth.jsonl", {"dev"}, "benign")
    synth_hn = _rows_split(ROOT / "eval/data/hard_negatives/synth.jsonl", {"dev"}, "hard_negative")
    real_ben = [r for r in pool_load(ROOT / "eval/data/realistic_dev/benign.jsonl") if r.get("split") == "dev"]
    real_hn = [r for r in pool_load(ROOT / "eval/data/realistic_dev/hard_negatives.jsonl") if r.get("split") == "dev"]
    random.shuffle(synth_atk)
    base_atk = synth_atk[:80]
    base_neg = synth_ben[:60] + synth_hn[:40] + real_ben[:80] + real_hn[:40]
    random.shuffle(base_neg)
    base_neg = base_neg[:220]

    atk_a, neg_a = base_atk[:80], base_neg[:210]
    rt_atk = pool_load(ROOT / "eval/data/dev_redteam/batch_a_attacks.jsonl")
    rt_hn = pool_load(ROOT / "eval/data/dev_redteam/batch_b_hard_negatives.jsonl")
    rt_ben = pool_load(ROOT / "eval/data/dev_redteam/batch_c_benign.jsonl")
    atk_b = (base_atk + rt_atk)[:120]
    neg_b = (base_neg + rt_ben + rt_hn)[:320]

    atk_c, neg_c = build_curve_c_pool(ROOT, seed=SEED)
    lm_only_atk = pool_load(ROOT / "eval/data/length_matched/attacks.jsonl")[:120]
    lm_only_neg = pool_load(ROOT / "eval/data/length_matched/benign.jsonl")[:160] + pool_load(
        ROOT / "eval/data/length_matched/hard_negatives.jsonl"
    )[:160]
    return {
        "A": (atk_a, neg_a),
        "B": (atk_b, neg_b),
        "C": (atk_c, neg_c),
        "operating_curve_v20_lm_only": (lm_only_atk, lm_only_neg),
    }


def _cascade_gating(atk: list[dict], neg: list[dict]) -> dict:
    os.environ["PROMPTSHIELD_POLICY"] = "template"
    os.environ["JUDGE_DISABLE"] = "1"
    os.environ["JUDGE_CASCADE"] = "1"
    os.environ.pop("JUDGE_GRAY_ZONE_ONLY", None)
    reset_classifier_cache()
    scan_telemetry.reset()

    def rate(rows: list[dict], prefix: str) -> dict:
        consult = pref_hi = 0
        n = len(rows)
        for i, r in enumerate(rows):
            scan_telemetry.reset()
            _scan(_content(r), r.get("source_type") or "text", f"{prefix}_{i}")
            t = scan_telemetry.get()
            if t.get("cascade_on") and (t.get("consult_judge") or t.get("pref", 0) >= 0.15):
                consult += 1
            if t.get("pref", 0) >= float(
                (json.loads(POLICY_TEMPLATE.read_text()).get("judge") or {}).get("cascade", {}).get("prefilter_hi", 0.55)
            ):
                pref_hi += 1
        return {"n": n, "would_consult_or_prefilter": round(consult / max(1, n), 4), "pref_ge_hi": round(pref_hi / max(1, n), 4)}

    # With judge disabled, measure prefilter / gating that would fire under full cascade
    os.environ["JUDGE_DISABLE"] = "0"
    os.environ["JUDGE_CASCADE"] = "1"
    os.environ["JUDGE_FORCE_OFFLINE"] = "1"
    reset_classifier_cache()

    def gated(rows: list[dict], prefix: str) -> dict:
        consult = 0
        n = len(rows)
        for i, r in enumerate(rows):
            scan_telemetry.reset()
            _scan(_content(r), r.get("source_type") or "text", f"{prefix}_{i}")
            t = scan_telemetry.get()
            if t.get("consult_judge"):
                consult += 1
        return {"n": n, "consult_judge_rate": round(consult / max(1, n), 4)}

    return {
        "note": "full_cascade+offline; consult_judge rate (prefilter/long/gray paths)",
        "benign_dev": gated(neg[:80], "cg_b"),
        "attacks_dev": gated(atk[:80], "cg_a"),
    }


def main() -> None:
    os.environ["PROMPTSHIELD_POLICY"] = "template"
    os.environ.pop("JUDGE_DISABLE", None)
    os.environ["JUDGE_FORCE_OFFLINE"] = "1"
    os.environ["JUDGE_CASCADE"] = "0"
    reset_classifier_cache()

    pools = _build_pools()
    measured = {}
    for name, (atk, neg) in pools.items():
        measured[name] = _metrics(atk, neg, name)

    synth_atk = measured.get("A", {})
    atk80, neg80 = pools["A"][0], pools["A"][1]
    cascade = _cascade_gating(atk80, neg80)

    fit_report = ROOT / "eval/reports/fit_length_curves_v14.json"
    fit_hashes = {
        "default_yml_template_sha256": _sha(POLICY_TEMPLATE),
        "fit_script_policy_path_note": "fit_length_curves_v14 mutates default.yml during grid; FREEZE documents template hash after v1.4 claim",
    }
    if fit_report.exists():
        fr = json.loads(fit_report.read_text(encoding="utf-8"))
        fit_hashes["fit_A_ACTED_FPR"] = {
            k: fr.get("A_before_dev_redteam", {}).get("chosen", {}).get(k)
            for k in ("ACTED", "FPR", "n_atk", "n_neg")
        }
        fit_hashes["fit_C_ACTED_FPR"] = {
            k: fr.get("C_length_matched", {}).get("chosen", {}).get(k)
            for k in ("ACTED", "FPR", "n_atk", "n_neg")
        }

    out = {
        "seed": SEED,
        "policy": fit_hashes,
        "measured_template_no_judge": measured,
        "cascade_gating_synth_dev": cascade,
        "explanation": {
            "operating_curve_v20_vs_fit_C": (
                "operating_curve_v20 used length_matched attacks+benign only (n_atk=110 cap 120, n_neg=320 LM-only), "
                "not curve-C pool (80 synth dev attacks + LM mix to 120; neg includes synth+realistic dev base_neg). "
                "LM-only attacks are harder → lower ACTED; LM-only neg omits dev hard negatives → higher FPR."
            ),
            "active_policy": "Eval sets PROMPTSHIELD_POLICY=template to ignore apps/api/data/active_policy.yml version drift.",
            "fpr_le_2pct": "Grid in fit_length_curves_v14 found no point with FPR≤2% on curve C; claimed fit is min-FPR max-ACTED.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
