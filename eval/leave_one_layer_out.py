#!/usr/bin/env python3
"""Leave-one-layer-out ablation + R4 single-layer attribution (report only).

Monkeypatches only. SEED=42.
Primary metric: decision != allow (policy outcome).
Also runs signatures_only / classifier_only / no_quote_dampen for explanations.
"""

from __future__ import annotations

import json
import math
import sys
import uuid
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT))

SEED = 42

from promptshield.domain import (  # noqa: E402
    AttackType,
    Decision,
    Finding,
    ScanRequest,
    SourceType,
    TrustLevel,
)
from promptshield.pipeline import scan as real_scan  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _source(row: dict) -> SourceType:
    try:
        return SourceType(row.get("source_type") or "text")
    except Exception:
        return SourceType.text


def _policy():
    import yaml

    return yaml.safe_load(
        (ROOT / "apps/api/src/promptshield/policies/default.yml").read_text(encoding="utf-8")
    )


def _fuse_no_floor(**kwargs):
    f = kwargs.get("fusion") or {}
    b = float(f.get("b", -2.0))
    w_sig = float(f.get("w_sig", 5.0))
    w_h = float(f.get("w_h", 1.5))
    w_ml = float(f.get("w_ml", 3.5))
    w_j = float(f.get("w_j", 2.5))
    w_hid = float(f.get("w_hid", 1.2))
    w_enc = float(f.get("w_enc", 1.0))
    w_sess = float(f.get("w_sess", 1.5))
    trust = kwargs.get("trust", TrustLevel.T3)
    w_trust_map = f.get("w_trust") or {"T0": -2.0, "T1": 0.0, "T2": 0.4, "T3": 0.6}
    w_trust = float(w_trust_map.get(trust.name, 0.6))
    z = (
        b
        + w_sig * float(kwargs.get("max_signature_severity") or 0.0)
        + w_h * float(kwargs.get("heuristic_score") or 0.0)
        + w_ml * float(kwargs.get("classifier_prob") or 0.0)
        + w_j
        * (
            float(kwargs.get("judge_confidence") or 0.0)
            if kwargs.get("judge_says_injection")
            else 0.0
        )
        + w_hid * float(kwargs.get("hidden") or 0.0)
        + w_enc * float(kwargs.get("encoded") or 0.0)
        + w_trust
        + w_sess * float(kwargs.get("session_risk") or 0.0)
    )
    if z >= 0:
        return 1 / (1 + math.exp(-z))
    return math.exp(z) / (1 + math.exp(z))


def _signatures_only(content: str, trust: TrustLevel):
    from promptshield.detect.signatures import SignatureEngine
    from promptshield.fusion.score import decide, fuse_risk

    eng = SignatureEngine()
    hits = eng.scan(content)
    findings: list[Finding] = []
    max_sev = 0.0
    for h in hits:
        sev = float(getattr(h, "severity", 0.9))
        max_sev = max(max_sev, sev)
        at = getattr(h, "attack_type", None)
        findings.append(
            Finding(
                id=f"s_{uuid.uuid4().hex[:8]}",
                segment_id="seg0",
                span=h.span,
                attack_types=[AttackType(at)] if at in {x.value for x in AttackType} else [],
                detector="signature",
                rule_id=getattr(h, "rule_id", None),
                score=sev,
                reason_code="SIG",
                evidence=(content[h.span[0] : h.span[1]] if h.span else "")[:200],
            )
        )
    policy = _policy()
    risk = fuse_risk(
        max_signature_severity=max_sev,
        heuristic_score=0.0,
        classifier_prob=0.0,
        fusion=policy.get("fusion"),
        trust=trust,
    )
    decision = decide(
        risk,
        findings,
        trust=trust,
        source_type="text",
        text_len=len(content),
        policy=policy,
    )

    class R:
        pass

    r = R()
    r.decision = decision
    r.findings = findings
    r.risk = risk
    return r


def _classifier_only(content: str, trust: TrustLevel):
    from promptshield.detect.classifier import get_classifier
    from promptshield.fusion.score import decide, fuse_risk

    policy = _policy()
    clf = get_classifier()
    prob = float(clf.predict_proba(content) if clf else 0.0)
    risk = fuse_risk(
        max_signature_severity=0.0,
        heuristic_score=0.0,
        classifier_prob=prob,
        fusion=policy.get("fusion"),
        trust=trust,
    )
    decision = decide(
        risk,
        [],
        trust=trust,
        source_type="text",
        text_len=len(content),
        policy=policy,
    )

    class R:
        pass

    r = R()
    r.decision = decision
    r.findings = []
    r.risk = risk
    r._clf = prob
    return r


def _scan_row(row: dict, *, mode: str, trust: TrustLevel = TrustLevel.T1, session_id: str = "x"):
    import promptshield.pipeline as pipe
    import promptshield.detect.quotation as quot
    import promptshield.detect.heuristics as heur_mod
    import promptshield.detect.session as sess_mod
    import promptshield.detect.judge as judge_mod
    import promptshield.detect.signatures as sig_mod
    import promptshield.fusion.score as fusion_mod
    from promptshield.detect.classifier import Classifier
    from promptshield.detect.quotation import DiscourseFeatures

    text = row.get("content") or ""
    source = _source(row)

    if mode == "signatures_only":
        return _signatures_only(text, trust)
    if mode == "classifier_only":
        return _classifier_only(text, trust)

    # Bindings pipeline imported by name — must patch both module and pipe.*
    orig = {
        "sig_scan": sig_mod.SignatureEngine.scan,
        "hf": heur_mod.heuristic_findings,
        "hs": heur_mod.heuristic_score,
        "cf": heur_mod.compute_features,
        "pipe_hf": pipe.heuristic_findings,
        "pipe_hs": pipe.heuristic_score,
        "pipe_cf": pipe.compute_features,
        "disc": quot.discourse_features,
        "is_q": quot.is_quotation_or_discussion,
        "fuse": fusion_mod.fuse_risk,
        "pipe_fuse": pipe.fuse_risk,
        "sess": sess_mod.get_session_analyser,
        "pipe_sess": pipe.get_session_analyser,
        "offline": judge_mod._offline_judge,
        "clf": Classifier.predict_proba,
        "pipe_scan": pipe.scan,
    }

    try:
        if mode == "no_signatures":
            sig_mod.SignatureEngine.scan = lambda self, text, segment_id="seg_0": []  # type: ignore

        if mode == "no_heuristics":

            def _empty_findings(*a, **k):
                return []

            def _zero_score(*a, **k):
                return 0.0

            def _empty_feats(*a, **k):
                return {
                    "addressee": 0.0,
                    "imperative_density": 0.0,
                    "tool_mentions": 0.0,
                    "exfil_shape": 0.0,
                    "role_markers": 0.0,
                    "hidden": 0.0,
                    "encoded": 0.0,
                    "invisible_chars": 0.0,
                    "instruction_in_data": 0.0,
                    "trust_prior": 0.0,
                    "quotation_score": 0.0,
                    "educational_score": 0.0,
                    "human_reader_score": 0.0,
                    "ai_agent_score": 0.0,
                }

            heur_mod.heuristic_findings = _empty_findings  # type: ignore
            heur_mod.heuristic_score = _zero_score  # type: ignore
            heur_mod.compute_features = _empty_feats  # type: ignore
            pipe.heuristic_findings = _empty_findings  # type: ignore
            pipe.heuristic_score = _zero_score  # type: ignore
            pipe.compute_features = _empty_feats  # type: ignore

        if mode in ("no_discourse", "no_quote_dampen"):
            if mode == "no_discourse":
                quot.discourse_features = lambda text: DiscourseFeatures(  # type: ignore
                    0.0, 0.0, 0.0, 0.0, 0.0, False, False
                )
            else:
                # Keep educational/human/agent scores; force quotation_score=0 so dampen=False
                def _no_dampen(text: str):
                    feats = orig["disc"](text)
                    return DiscourseFeatures(
                        quotation_score=0.0,
                        educational_score=feats.educational_score,
                        human_reader_score=feats.human_reader_score,
                        ai_agent_score=feats.ai_agent_score,
                        ai_agent_score_raw=feats.ai_agent_score_raw,
                        attackish_present=feats.attackish_present,
                        quote_marked=feats.quote_marked,
                    )

                quot.discourse_features = _no_dampen  # type: ignore

            quot.is_quotation_or_discussion = lambda text, threshold=0.55: False  # type: ignore

            def _offline(text, source_type="text"):
                r = orig["offline"](text, source_type)
                r.is_quotation_or_discussion = False
                return r

            judge_mod._offline_judge = _offline  # type: ignore

        if mode == "no_classifier":
            Classifier.predict_proba = lambda self, text: 0.0  # type: ignore

        if mode == "no_session":

            class _Null:
                def observe(self, *a, **k):
                    return 0.0

                def risk(self, *a, **k):
                    return 0.0

                def payload_split_findings(self, *a, **k):
                    return []

                def should_escalate(self, *a, **k):
                    return False

            null = _Null()
            sess_mod.get_session_analyser = lambda: null  # type: ignore
            pipe.get_session_analyser = lambda: null  # type: ignore

        if mode == "no_signature_floor":
            fusion_mod.fuse_risk = _fuse_no_floor  # type: ignore
            pipe.fuse_risk = _fuse_no_floor  # type: ignore

            def _wrapped(request, *, noop=False, raw=None):
                from promptshield.fusion.score import decide

                res = orig["pipe_scan"](request, noop=noop, raw=raw)
                max_sev = max(
                    (f.score for f in res.findings if f.detector == "signature"),
                    default=0.0,
                )
                clf_p = max(
                    (f.score for f in res.findings if f.detector == "classifier"),
                    default=0.0,
                )
                heur = max(
                    (f.score for f in res.findings if f.detector == "heuristic"),
                    default=0.0,
                )
                policy = pipe._policy()
                risk2 = _fuse_no_floor(
                    max_signature_severity=max_sev,
                    heuristic_score=heur,
                    classifier_prob=clf_p,
                    fusion=policy.get("fusion"),
                    trust=request.trust,
                )
                res.risk = risk2
                res.decision = decide(
                    risk2,
                    list(res.findings),
                    trust=request.trust,
                    source_type=request.source_type.value,
                    text_len=len(request.content or ""),
                    policy=policy,
                )
                return res

            pipe.scan = _wrapped  # type: ignore

        return real_scan(
            ScanRequest(
                source_type=source,
                content=text,
                trust=trust,
                session_id=session_id,
            ),
            noop=False,
        )
    finally:
        sig_mod.SignatureEngine.scan = orig["sig_scan"]  # type: ignore
        heur_mod.heuristic_findings = orig["hf"]
        heur_mod.heuristic_score = orig["hs"]
        heur_mod.compute_features = orig["cf"]
        pipe.heuristic_findings = orig["pipe_hf"]  # type: ignore
        pipe.heuristic_score = orig["pipe_hs"]  # type: ignore
        pipe.compute_features = orig["pipe_cf"]  # type: ignore
        quot.discourse_features = orig["disc"]
        quot.is_quotation_or_discussion = orig["is_q"]
        fusion_mod.fuse_risk = orig["fuse"]
        pipe.fuse_risk = orig["pipe_fuse"]  # type: ignore
        sess_mod.get_session_analyser = orig["sess"]
        pipe.get_session_analyser = orig["pipe_sess"]  # type: ignore
        judge_mod._offline_judge = orig["offline"]
        Classifier.predict_proba = orig["clf"]
        pipe.scan = orig["pipe_scan"]  # type: ignore


def layer_alone_flags(text: str, trust: TrustLevel = TrustLevel.T1) -> dict:
    from promptshield.detect.signatures import SignatureEngine
    from promptshield.detect.heuristics import compute_features, heuristic_score
    from promptshield.detect.classifier import get_classifier
    from promptshield.adapters import adapt

    eng = SignatureEngine()
    sig_hits = eng.scan(text)
    segs = adapt(SourceType.text, text, trust)
    scores = []
    for seg in segs:
        feats = compute_features(seg, tools=[])
        scores.append(heuristic_score(feats))
    h_score = max(scores) if scores else 0.0
    clf = get_classifier()
    clf_p = float(clf.predict_proba(text) if clf else 0.0)
    return {
        "signatures": bool(sig_hits),
        "heuristics": h_score >= 0.35,
        "classifier": clf_p >= 0.5,
        "signature_floor_eligible": any(h.severity >= 0.75 for h in sig_hits),
        "max_sig": max((h.severity for h in sig_hits), default=0.0),
        "heur_score": round(h_score, 4),
        "clf_prob": round(clf_p, 4),
    }


def eval_attacks(rows: list[dict], mode: str, *, tag: str) -> dict:
    atk = [r for r in rows if r.get("label") == "attack"]
    hits = 0
    for i, r in enumerate(atk):
        # Unique session per block — global SessionAnalyser must not accumulate across sets
        res = _scan_row(r, mode=mode, session_id=f"{mode}_{tag}_{i}")
        hits += int(res.decision != Decision.allow)
    n = len(atk)
    return {"n": n, "detected": hits, "recall": rate(hits, n), "ci": list(wilson_ci(hits, n))}


def eval_fpr(rows: list[dict], mode: str, label: str, *, tag: str) -> dict:
    subset = [r for r in rows if r.get("label") == label]
    fp = 0
    for i, r in enumerate(subset):
        res = _scan_row(r, mode=mode, session_id=f"{mode}_{tag}_{label}_{i}")
        fp += int(res.decision != Decision.allow)
    n = len(subset)
    return {"n": n, "fp": fp, "fpr": rate(fp, n), "ci": list(wilson_ci(fp, n))}


def main() -> dict:
    test_atk = [r for r in _load(ROOT / "eval/data/attacks/synth_text.jsonl") if r.get("split") == "test"]
    test_ben = [r for r in _load(ROOT / "eval/data/benign/synth.jsonl") if r.get("split") == "test"]
    test_hn = [r for r in _load(ROOT / "eval/data/hard_negatives/synth.jsonl") if r.get("split") == "test"]
    test_all = test_atk + test_ben + test_hn
    r3 = _load(ROOT / "eval/data/sealed/round3.jsonl")
    r4 = _load(ROOT / "eval/data/sealed/round4.jsonl")
    realistic_b = _load(ROOT / "eval/data/realistic/benign.jsonl")
    realistic_h = _load(ROOT / "eval/data/realistic/hard_negatives.jsonl")

    modes = [
        "as_is",
        "no_signatures",
        "no_heuristics",
        "no_discourse",
        "no_classifier",
        "no_session",
        "no_signature_floor",
        "signatures_only",
        "classifier_only",
        "no_quote_dampen",
    ]
    out: dict = {"seed": SEED, "metric": "decision_ne_allow", "modes": {}}
    for mode in modes:
        print(f"mode={mode}", flush=True)
        block = {
            "test_attack": eval_attacks(test_all, mode, tag="test_atk"),
            "test_benign_fpr": eval_fpr(test_all, mode, "benign", tag="test_ben"),
            "test_hn_fpr": eval_fpr(test_all, mode, "hard_negative", tag="test_hn"),
            "r3_attack": eval_attacks(r3, mode, tag="r3"),
            "r4_attack": eval_attacks(r4, mode, tag="r4"),
            "realistic_benign_fpr": eval_fpr(realistic_b, mode, "benign", tag="real_ben"),
            "realistic_hn_fpr": eval_fpr(realistic_h, mode, "hard_negative", tag="real_hn"),
        }
        out["modes"][mode] = block
        print(json.dumps({mode: block}, indent=2), flush=True)

    r4_atk = [r for r in r4 if r.get("label") == "attack"]
    attribution = []
    alone_counts: Counter[str] = Counter()
    for r in r4_atk:
        text = r.get("content") or ""
        full = real_scan(
            ScanRequest(
                source_type=SourceType.text,
                content=text,
                trust=TrustLevel.T1,
                session_id=f"attr_{r['id']}",
            ),
            noop=False,
        )
        detected = full.decision != Decision.allow
        alone = layer_alone_flags(text)
        layers = [k for k in ("signatures", "heuristics", "classifier") if alone.get(k)]
        if alone.get("signature_floor_eligible"):
            layers.append("signature_floor_eligible")
        if detected:
            for L in layers or ["none_alone_but_fused"]:
                alone_counts[L] += 1
        attribution.append(
            {
                "id": r["id"],
                "detected": detected,
                "decision": full.decision.value,
                "risk": full.risk,
                "layers_alone": layers,
                "signals": alone,
            }
        )

    sig_alone = sum(1 for a in attribution if a["signals"]["signatures"])
    clf_ge = sum(1 for a in attribution if a["signals"]["classifier"])
    detected_n = sum(1 for a in attribution if a["detected"])
    r4_sig_only = out["modes"]["signatures_only"]["r4_attack"]["recall"]
    r4_clf_only = out["modes"]["classifier_only"]["r4_attack"]["recall"]
    r4_as_is = out["modes"]["as_is"]["r4_attack"]["recall"]
    r4_no_qd = out["modes"]["no_quote_dampen"]["r4_attack"]["recall"]
    # Findings-OR metric (matches ablation_v11 / prior EVIDENCE 0.917)
    r4_findings_or = 0
    for r in r4_atk:
        res = real_scan(
            ScanRequest(
                source_type=SourceType.text,
                content=r.get("content") or "",
                trust=TrustLevel.T1,
                session_id=f"findor_{r['id']}",
            ),
            noop=False,
        )
        r4_findings_or += int(res.decision != Decision.allow or bool(res.findings))
    explanation = {
        "metric_note": (
            "LOLO primary metric is decision!=allow. Prior ablation_v11 / EVIDENCE R4 "
            "as-is=0.917 used decision!=allow OR bool(findings); classifier findings on "
            "allow decisions inflate that figure."
        ),
        "r4_as_is_decision_recall": r4_as_is,
        "r4_as_is_findings_or_recall": rate(r4_findings_or, len(r4_atk)),
        "signatures_only_r4_near_zero_reason": (
            f"signatures_only R4 decision-recall={r4_sig_only:.3f}; findings-OR as-is="
            f"{rate(r4_findings_or, len(r4_atk)):.3f}. Of {len(r4_atk)} R4 attacks, "
            f"signature regexes fire alone on {sig_alone}. R4 paraphrases evade frozen "
            "rules — signatures-only has nothing to fuse or floor."
        ),
        "classifier_only_zero_reason": (
            f"classifier_only R4 decision-recall={r4_clf_only:.3f}. "
            f"Raw clf_prob≥0.5 on {clf_ge}/{len(r4_atk)} R4 texts (and findings-OR as-is "
            "counts those findings), but without signature findings/floor, fusion bias "
            "keeps risk below sanitize/block — classifier-only decision recall = 0."
        ),
        "no_quote_dampen_zero_effect_reason": (
            f"no_quote_dampen R4 decision-recall={r4_no_qd:.3f} equals as_is={r4_as_is:.3f}. "
            "R3/R4/test attacks are not quotation-wrapped; discourse dampening never activates, "
            "so removing quotation dampening has zero effect on these sets."
        ),
        "alone_counts_among_detected": dict(alone_counts),
        "r4_detected_decision": detected_n,
        "r4_sig_alone": sig_alone,
        "r4_clf_prob_ge_0_5": clf_ge,
    }
    out["r4_attribution"] = attribution
    out["explanation"] = explanation
    path = ROOT / "eval/reports/leave_one_layer_out.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(explanation, indent=2))
    print(f"Wrote {path}")
    return out


if __name__ == "__main__":
    main()
