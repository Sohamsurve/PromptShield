#!/usr/bin/env python3
"""Ablation on test / R3 / R4 without changing checked-in code or weights.

Modes:
  (a) as-is
  (b) markers stripped from text
  (c) signatures only
  (d) classifier only
  (e) without quotation dampening
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(ROOT))

from promptshield.domain import Decision, ScanRequest, SourceType, TrustLevel  # noqa: E402
from promptshield.pipeline import scan as real_scan  # noqa: E402

from eval.metrics import rate, wilson_ci  # noqa: E402

MARKER_RE = re.compile(
    r"(?i)\s*(?:Unique=\d+|Variant\s+\d+|Case\s+\d+|\[r2:[^\]]+\])\s*"
)


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _strip_markers(text: str) -> str:
    return MARKER_RE.sub(" ", text or "").strip()


def _flagged(result) -> bool:
    return result.decision != Decision.allow or bool(result.findings)


def _scan(text: str, *, mode: str, trust: TrustLevel = TrustLevel.T1) -> object:
    content = _strip_markers(text) if mode == "b_markers_stripped" else text
    import promptshield.pipeline as pipe
    import promptshield.detect.quotation as quot
    import promptshield.detect.classifier as clf_mod

    # Save originals
    orig_sig = pipe.SignatureEngine
    orig_disc = quot.discourse_features
    orig_is_quote = quot.is_quotation_or_discussion
    orig_clf = getattr(clf_mod, "predict_proba", None)

    try:
        if mode == "c_signatures_only":
            # Zero classifier + disable quotation dampening path by making dampen False
            # and zero heuristics via wrapping scan post-process is hard — instead
            # monkeypatch fuse inputs by wrapping scan and post-filtering findings.
            result = real_scan(
                ScanRequest(source_type=SourceType.text, content=content, trust=trust),
                noop=False,
            )
            # Recompute: keep only signature findings; risk from signatures via re-scan
            # using fuse_risk directly
            from promptshield.fusion.score import fuse_risk, decide
            from promptshield.detect.signatures import SignatureEngine

            eng = SignatureEngine()
            hits = eng.scan(content)
            findings = [
                f
                for f in result.findings
                if f.detector == "signature"
            ]
            max_sev = max((f.score for f in findings), default=0.0)
            # Also build findings from engine if pipeline dropped them
            if not findings and hits:
                from promptshield.domain import Finding, AttackType
                import uuid

                for h in hits:
                    findings.append(
                        Finding(
                            id=f"s_{uuid.uuid4().hex[:8]}",
                            segment_id="seg0",
                            span=h.span,
                            attack_types=[AttackType(h.attack_type)] if hasattr(h, "attack_type") else [],
                            detector="signature",
                            rule_id=getattr(h, "rule_id", None),
                            score=getattr(h, "severity", 0.9),
                            reason_code="SIG",
                            evidence=(content[h.span[0] : h.span[1]] if h.span else "")[:200],
                        )
                    )
                    max_sev = max(max_sev, getattr(h, "severity", 0.9))
            policy = pipe.load_policy() if hasattr(pipe, "load_policy") else {}
            try:
                from promptshield.policies import load_policy

                policy = load_policy()
            except Exception:
                import yaml

                policy = yaml.safe_load(
                    (ROOT / "apps/api/src/promptshield/policies/default.yml").read_text()
                )
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

        if mode == "d_classifier_only":
            from promptshield.detect.classifier import get_classifier
            from promptshield.fusion.score import fuse_risk, decide
            import yaml

            policy = yaml.safe_load(
                (ROOT / "apps/api/src/promptshield/policies/default.yml").read_text()
            )
            clf = get_classifier()
            prob = float(clf.predict_proba(content) if clf else 0.0)
            risk = fuse_risk(
                max_signature_severity=0.0,
                heuristic_score=0.0,
                classifier_prob=prob,
                fusion=policy.get("fusion"),
                trust=trust,
            )
            # No signature floor path — classifier alone
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

        if mode == "e_no_quotation_dampen":
            def _no_dampen(text: str):
                feats = orig_disc(text)
                from promptshield.detect.quotation import DiscourseFeatures

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

        return real_scan(
            ScanRequest(source_type=SourceType.text, content=content, trust=trust),
            noop=False,
        )
    finally:
        quot.discourse_features = orig_disc
        quot.is_quotation_or_discussion = orig_is_quote


def eval_attacks(rows: list[dict], mode: str) -> dict:
    atk = [r for r in rows if r.get("label") == "attack"]
    hits = 0
    for r in atk:
        text = r.get("content") or ""
        res = _scan(text, mode=mode)
        hits += int(_flagged(res))
    n = len(atk)
    return {"n": n, "recall": rate(hits, n), "ci": list(wilson_ci(hits, n)), "detected": hits}


def eval_fpr(rows: list[dict], mode: str, label: str) -> dict:
    subset = [r for r in rows if r.get("label") == label]
    fp = 0
    for r in subset:
        res = _scan(r.get("content") or "", mode=mode)
        fp += int(res.decision != Decision.allow)
    n = len(subset)
    return {"n": n, "fpr": rate(fp, n), "ci": list(wilson_ci(fp, n)), "fp": fp}


def main() -> dict:
    test = _load(ROOT / "eval" / "data" / "attacks" / "synth_text.jsonl")
    # also benign/HN from synth for FPR on same split
    benign = _load(ROOT / "eval" / "data" / "benign" / "synth.jsonl")
    hn = _load(ROOT / "eval" / "data" / "hard_negatives" / "synth.jsonl")
    test_all = [r for r in test + benign + hn if r.get("split") == "test"]
    r3 = _load(ROOT / "eval" / "data" / "sealed" / "round3.jsonl")
    r4 = _load(ROOT / "eval" / "data" / "sealed" / "round4.jsonl")

    modes = [
        ("a_as_is", "a"),
        ("b_markers_stripped", "b"),
        ("c_signatures_only", "c"),
        ("d_classifier_only", "d"),
        ("e_no_quotation_dampen", "e"),
    ]
    out: dict = {}
    for mode_name, _ in modes:
        print(f"running {mode_name}...", flush=True)
        block = {
            "test_attack": eval_attacks(test_all, mode_name),
            "test_benign_fpr": eval_fpr(test_all, mode_name, "benign"),
            "test_hn_fpr": eval_fpr(test_all, mode_name, "hard_negative"),
            "r3_attack": eval_attacks(r3, mode_name),
            "r4_attack": eval_attacks(r4, mode_name),
        }
        # R3/R4 may not have benign — skip
        out[mode_name] = block
        print(json.dumps({mode_name: block}, indent=2), flush=True)

    path = ROOT / "eval" / "reports" / "ablation_v11.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {path}")
    return out


if __name__ == "__main__":
    main()
