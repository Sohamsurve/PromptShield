"""Fusion + policy decision (README §5.8). Graded classifier path (v1.3)."""

from __future__ import annotations

import math
from typing import Any

from promptshield.domain import Decision, Finding, TrustLevel


def sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1 / (1 + ez)
    ez = math.exp(z)
    return ez / (1 + ez)


def fuse_risk(
    *,
    max_signature_severity: float = 0.0,
    heuristic_score: float = 0.0,
    classifier_prob: float = 0.0,
    judge_confidence: float = 0.0,
    judge_says_injection: bool = False,
    hidden: float = 0.0,
    encoded: float = 0.0,
    trust: TrustLevel = TrustLevel.T3,
    session_risk: float = 0.0,
    fusion: dict[str, Any] | None = None,
) -> float:
    f = fusion or {}
    b = float(f.get("b", -2.0))
    w_sig = float(f.get("w_sig", 5.0))
    w_h = float(f.get("w_h", 1.5))
    w_ml = float(f.get("w_ml", 3.5))
    w_j = float(f.get("w_j", 2.5))
    w_hid = float(f.get("w_hid", 1.2))
    w_enc = float(f.get("w_enc", 1.0))
    w_sess = float(f.get("w_sess", 1.5))
    w_trust_map = f.get("w_trust") or {"T0": -2.0, "T1": 0.0, "T2": 0.4, "T3": 0.6}
    w_trust = float(w_trust_map.get(trust.name, w_trust_map.get(str(int(trust)), 0.6)))

    z = (
        b
        + w_sig * max_signature_severity
        + w_h * heuristic_score
        + w_ml * classifier_prob
        + w_j * (judge_confidence if judge_says_injection else 0.0)
        + w_hid * hidden
        + w_enc * encoded
        + w_trust
        + w_sess * session_risk
    )
    risk = sigmoid(z)
    if max_signature_severity >= 0.75:
        risk = max(risk, 0.8)
    return risk


def _span_localised(f: Finding, text_len: int) -> bool:
    if not f.span or text_len <= 0:
        return False
    lo, hi = f.span
    if hi <= lo:
        return False
    # Localised = covers < 85% of the document
    return (hi - lo) < int(0.85 * text_len)


def decide(
    risk: float,
    findings: list[Finding],
    *,
    trust: TrustLevel,
    source_type: str,
    text_len: int,
    high_impact: bool = False,
    policy: dict[str, Any] | None = None,
    residual_risk: float | None = None,
) -> Decision:
    policy = policy or {}
    sources = policy.get("sources") or {}
    p = sources.get(source_type) or sources.get("text") or {
        "block": 0.92,
        "quarantine": 0.70,
        "sanitize_span": 0.75,
        "escalate_band": [0.55, 0.70],
    }
    block = float(p.get("block", 0.92))
    quarantine = float(p.get("quarantine", 0.70))
    sanitize_span = float(p.get("sanitize_span", 0.75))
    escalate_band = p.get("escalate_band") or [0.55, 0.70]
    max_removal = float(policy.get("max_removal_ratio", 0.40))

    # Graded classifier thresholds (decision-level fit may overwrite)
    graded = policy.get("clf_graded") or {}
    clf_sanitize = float(graded.get("sanitize", 0.55))
    clf_quarantine = float(graded.get("quarantine", 0.70))
    clf_block = float(graded.get("block", 0.95))

    clf_findings = [f for f in findings if f.detector == "classifier"]
    max_clf = max((f.score for f in clf_findings), default=0.0)
    local_clf = [f for f in clf_findings if _span_localised(f, text_len)]
    unlocal_clf = [f for f in clf_findings if f not in local_clf]

    # Block only on high confidence (fused risk or very high clf)
    if risk >= block or max_clf >= clf_block:
        return Decision.block

    # Sanitise localised spans (signature/heuristic/classifier) under removal budget
    spans = [f for f in findings if f.span and f.score >= sanitize_span]
    # Also allow classifier localised spans at clf_sanitize threshold
    for f in local_clf:
        if f.score >= clf_sanitize and f not in spans:
            spans.append(f)
    if spans and text_len > 0:
        covered = sum(max(0, (f.span[1] - f.span[0])) for f in spans if f.span)
        ratio = covered / text_len
        if ratio <= max_removal:
            if residual_risk is not None and trust.value >= TrustLevel.T2 and residual_risk >= quarantine:
                return Decision.quarantine
            if trust.value >= TrustLevel.T2 and residual_risk is None and risk >= quarantine:
                return Decision.quarantine
            return Decision.sanitize

    # Quarantine / spotlight when classifier fires but span is not localised
    if unlocal_clf and max_clf >= clf_quarantine:
        return Decision.quarantine

    if risk >= quarantine:
        return Decision.quarantine

    lo, hi = float(escalate_band[0]), float(escalate_band[1])
    if lo <= risk <= hi and high_impact:
        return Decision.escalate

    return Decision.allow
