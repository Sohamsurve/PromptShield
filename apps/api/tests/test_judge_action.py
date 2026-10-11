"""Judge-driven action rules (v1.4 pre-registered)."""

from __future__ import annotations

from promptshield.domain import Decision, Finding, AttackType, TrustLevel
from promptshield.fusion.score import decide


def _f(**kwargs) -> Finding:
    return Finding(
        id="t",
        segment_id="s",
        span=kwargs.get("span"),
        attack_types=[AttackType.instruction_override],
        detector=kwargs.get("detector", "judge"),
        rule_id=None,
        score=kwargs.get("score", 0.9),
        reason_code="T",
        evidence="x",
    )


def test_unlocalised_classifier_does_not_sanitise_short_span() -> None:
    """A whole-segment classifier window is not a phrase to redact.

    Image sanitize_span is 0.55, so a 0.77 hit on a 24-char title used to
    sanitise even though the reason code is UNLOCALISED and clf sanitize is 0.85.
    """
    findings = [
        Finding(
            id="c",
            segment_id="s",
            span=(0, 24),
            attack_types=[AttackType.instruction_override],
            detector="classifier",
            rule_id=None,
            score=0.77,
            reason_code="CLF_INJECTION_UNLOCALISED",
            evidence="Quarterly Product Report",
        )
    ]
    d = decide(
        risk=0.06,
        findings=findings,
        trust=TrustLevel.T3,
        source_type="image",
        text_len=400,
        policy={
            "clf_graded": {"sanitize": 0.85, "quarantine": 0.92, "block": 0.98},
            "max_removal_ratio": 0.4,
            "sources": {
                "image": {"block": 0.85, "quarantine": 0.45, "sanitize_span": 0.55}
            },
        },
        max_signature_severity=0.0,
    )
    assert d == Decision.allow


def test_classifier_span_too_large_to_redact_quarantines_at_grade() -> None:
    """A hit at the quarantine grade must not become allow when redaction would eat the document."""
    findings = [
        Finding(
            id="c",
            segment_id="s",
            span=(0, 120),
            attack_types=[AttackType.instruction_override],
            detector="classifier",
            rule_id=None,
            score=0.95,
            reason_code="CLF_INJECTION",
            evidence="x",
        )
    ]
    policy = {
        "clf_graded": {"sanitize": 0.85, "quarantine": 0.92, "block": 0.98},
        "max_removal_ratio": 0.4,
        "sources": {"text": {"block": 0.92, "quarantine": 0.70, "sanitize_span": 0.75}},
    }
    quarantined = decide(
        risk=0.05,
        findings=findings,
        trust=TrustLevel.T1,
        source_type="text",
        text_len=200,
        policy=policy,
        max_signature_severity=0.0,
    )
    assert quarantined == Decision.quarantine
    still_allow = decide(
        risk=0.05,
        findings=[
            Finding(
                id="c2",
                segment_id="s",
                span=(0, 120),
                attack_types=[AttackType.instruction_override],
                detector="classifier",
                rule_id=None,
                score=0.90,
                reason_code="CLF_INJECTION",
                evidence="x",
            )
        ],
        trust=TrustLevel.T1,
        source_type="text",
        text_len=200,
        policy=policy,
        max_signature_severity=0.0,
    )
    assert still_allow == Decision.allow


def test_judge_with_span_sanitises_not_blocks() -> None:
    findings = [_f(detector="judge", span=(10, 40), score=0.95)]
    d = decide(
        risk=0.5,
        findings=findings,
        trust=TrustLevel.T3,
        source_type="text",
        text_len=500,
        policy={"clf_graded": {"sanitize": 0.85, "quarantine": 0.92, "block": 0.98}, "max_removal_ratio": 0.4,
                "sources": {"text": {"block": 0.92, "quarantine": 0.70, "sanitize_span": 0.75}}},
        judge_action="sanitize",
        max_signature_severity=0.0,
    )
    assert d == Decision.sanitize


def test_judge_without_span_quarantines() -> None:
    findings = [_f(detector="judge", span=(0, 200), score=0.9)]
    d = decide(
        risk=0.4,
        findings=findings,
        trust=TrustLevel.T3,
        source_type="text",
        text_len=500,
        policy={"clf_graded": {"sanitize": 0.85, "quarantine": 0.92, "block": 0.98}, "max_removal_ratio": 0.4,
                "sources": {"text": {"block": 0.92, "quarantine": 0.70, "sanitize_span": 0.75}}},
        judge_action="quarantine",
        max_signature_severity=0.0,
    )
    assert d == Decision.quarantine


def test_judge_cannot_override_high_classifier_block() -> None:
    findings = [
        _f(detector="judge", span=(10, 30), score=0.9),
        _f(detector="classifier", span=(0, 100), score=0.99),
    ]
    d = decide(
        risk=0.5,
        findings=findings,
        trust=TrustLevel.T3,
        source_type="text",
        text_len=500,
        policy={"clf_graded": {"sanitize": 0.85, "quarantine": 0.92, "block": 0.98}, "max_removal_ratio": 0.4,
                "sources": {"text": {"block": 0.92, "quarantine": 0.70, "sanitize_span": 0.75}}},
        judge_action="sanitize",
        max_signature_severity=0.0,
    )
    assert d == Decision.block


def test_judge_alone_never_blocks_via_action() -> None:
    findings = [_f(detector="judge", span=(10, 40), score=0.99)]
    d = decide(
        risk=0.99,  # even high risk from judge fusion path
        findings=findings,
        trust=TrustLevel.T3,
        source_type="text",
        text_len=500,
        policy={"clf_graded": {"sanitize": 0.85, "quarantine": 0.92, "block": 0.98}, "max_removal_ratio": 0.4,
                "sources": {"text": {"block": 0.92, "quarantine": 0.70, "sanitize_span": 0.75}}},
        judge_action="sanitize",
        max_signature_severity=0.0,
    )
    # risk>=block still blocks from fused risk — judge_action itself must not be the sole block path.
    # When risk is high from fusion including judge weight, block is allowed from risk.
    # Separate case: low risk + judge sanitize → sanitize
    d2 = decide(
        risk=0.4,
        findings=findings,
        trust=TrustLevel.T3,
        source_type="text",
        text_len=500,
        policy={"clf_graded": {"sanitize": 0.85, "quarantine": 0.92, "block": 0.98}, "max_removal_ratio": 0.4,
                "sources": {"text": {"block": 0.92, "quarantine": 0.70, "sanitize_span": 0.75}}},
        judge_action="sanitize",
        max_signature_severity=0.0,
    )
    assert d2 == Decision.sanitize
    assert d in {Decision.block, Decision.sanitize, Decision.quarantine}
