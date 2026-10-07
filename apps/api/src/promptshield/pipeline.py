"""Scan pipeline — adapt → canonicalise/decode → signatures → fuse → neutralise."""

from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from promptshield.adapters import adapt
from promptshield.detect.classifier import get_classifier, should_run_classifier
from promptshield.detect.heuristics import compute_features, heuristic_findings, heuristic_score
from promptshield.detect.judge import judge_segment
from promptshield.detect.session import get_session_analyser
from promptshield.detect.signatures import SignatureEngine
from promptshield.domain import (
    AttackType,
    Decision,
    Finding,
    Location,
    ScanRequest,
    ScanResult,
    Segment,
    SegmentSummary,
    SourceType,
    TrustLevel,
)
from promptshield.fusion.score import decide, fuse_risk
from promptshield.neutralize.redact import redact_spans, spotlight
from promptshield.normalize.decode import decode_recursive
from promptshield.normalize.unicode import canonicalize

# Sealed template path (FREEZE-hashed). Runtime may override via active_policy.yml.
POLICY_PATH = Path(__file__).resolve().parent / "policies" / "default.yml"


def _policy() -> dict[str, Any]:
    from promptshield.api.policy_store import resolve_policy_path

    path = resolve_policy_path()
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=1)
def _engine() -> SignatureEngine:
    return SignatureEngine()


def _identity_offset_map(text: str) -> list[int]:
    return list(range(len(text)))


def _segment_summaries(segments: list[Segment]) -> list[SegmentSummary]:
    return [
        SegmentSummary(
            id=s.id,
            kind=s.location.kind,
            hidden=bool(s.location.hidden_reason),
            hidden_reason=s.location.hidden_reason,
            text_preview=s.text[:120],
        )
        for s in segments
    ]


def _already_sanitized(text: str) -> bool:
    if "[removed: suspected instruction]" not in text:
        return False
    residual = text.replace("[removed: suspected instruction]", " ")
    return not any(
        k in residual.lower()
        for k in (
            "ignore previous",
            "ignore prior",
            "system prompt",
            "send_email",
            "you are now",
            "decode this",
        )
    )


def scan(
    request: ScanRequest,
    *,
    noop: bool = False,
    raw: bytes | None = None,
) -> ScanResult:
    t0 = time.perf_counter()
    scan_id = f"scn_{uuid.uuid4().hex[:8]}"
    content = request.content or ""
    payload: bytes | str = raw if raw is not None else content
    policy = _policy()
    degraded: list[str] = []

    if noop:
        segments = adapt(request.source_type, payload, request.trust)
        return ScanResult(
            scan_id=scan_id,
            decision=Decision.allow,
            risk=0.0,
            attack_types=[],
            findings=[],
            segments=_segment_summaries(segments),
            sanitized_text=content if isinstance(payload, str) else None,
            latency_ms={"total": round((time.perf_counter() - t0) * 1000, 3)},
            policy_version=str(policy.get("version", "1")),
            degraded=["noop_firewall"],
        )

    t_adapt = time.perf_counter()
    try:
        segments = adapt(request.source_type, payload, request.trust)
    except Exception:
        # Fail soft for T3: plain text + quarantine later via degraded
        degraded.append("adapter")
        text_fallback = content if content else (
            raw.decode("utf-8", errors="replace") if raw else ""
        )
        segments = adapt(SourceType.text, text_fallback, request.trust)

    # Surface OCR unavailability as degraded
    if any((s.location.hidden_reason or "") == "img:ocr_unavailable" for s in segments):
        degraded.append("ocr_unavailable")

    decoded_segments: list[Segment] = []
    for seg in segments:
        for child in decode_recursive(seg.canonical or seg.text):
            decoded_segments.append(
                Segment(
                    id=f"seg_{uuid.uuid4().hex[:8]}",
                    source_id=seg.source_id,
                    text=child.text,
                    canonical=canonicalize(child.text).canonical,
                    offset_map=_identity_offset_map(child.text),
                    trust=seg.trust,
                    location=Location(kind="decoded", hidden_reason="decoded"),
                    decoded_from=list(child.decoded_from),
                    parent_id=seg.id,
                )
            )
    segments.extend(decoded_segments)
    adapt_ms = (time.perf_counter() - t_adapt) * 1000

    # Joined text for redaction / length (visible+hidden segment texts)
    joined = "\n".join(s.text for s in segments if s.text)
    redact_base = content if content else joined

    # Idempotence short-circuit: already-redacted text should not SANITIZE again
    if isinstance(payload, str) and _already_sanitized(payload):
        return ScanResult(
            scan_id=scan_id,
            decision=Decision.allow,
            risk=0.05,
            attack_types=[],
            findings=[],
            segments=_segment_summaries(segments),
            sanitized_text=payload,
            latency_ms={"adapt": round((time.perf_counter() - t0) * 1000, 3), "total": round((time.perf_counter() - t0) * 1000, 3)},
            policy_version=str(policy.get("version", "1")),
            degraded=degraded,
        )

    t_sig = time.perf_counter()
    engine = _engine()
    tools = list(request.agent_context.tools) if request.agent_context else []
    findings: list[Finding] = []
    feat_scores: list[float] = []
    for seg in segments:
        hay = seg.canonical or seg.text
        hits = engine.scan(hay, segment_id=seg.id)
        for h in hits:
            if h.span and seg.offset_map and h.span[1] <= len(seg.offset_map):
                start, end = h.span
                h.span = (
                    seg.offset_map[start],
                    seg.offset_map[min(end - 1, len(seg.offset_map) - 1)] + 1,
                )
            if seg.trust.value >= TrustLevel.T2 and AttackType.indirect_injection not in h.attack_types:
                h.attack_types = list(h.attack_types) + [AttackType.indirect_injection]
            findings.append(h)
        feats = compute_features(seg, tools=tools)
        feat_scores.append(heuristic_score(feats))
    findings.extend(heuristic_findings(segments, tools=tools))
    sig_ms = (time.perf_counter() - t_sig) * 1000

    # Session analyser (decay + payload-split rescan)
    session_risk = 0.0
    if request.session_id:
        analyser = get_session_analyser()
        sess_cfg = policy.get("session") or {}
        if sess_cfg.get("lambda") is not None:
            analyser.lam = float(sess_cfg["lambda"])
        if sess_cfg.get("threshold") is not None:
            analyser.threshold = float(sess_cfg["threshold"])
        if sess_cfg.get("window") is not None:
            analyser.window = int(sess_cfg["window"])
        user_blob = " ".join((s.text or "")[:400] for s in segments)[:800]
        scores = [f.score for f in findings]
        session_risk = analyser.observe(
            request.session_id, finding_scores=scores, user_text=user_blob
        )
        for hit in analyser.payload_split_findings(request.session_id):
            hit.detector = "session"
            hit.reason_code = hit.reason_code or "SESSION_PAYLOAD_SPLIT"
            if AttackType.multi_step_jailbreak not in hit.attack_types:
                hit.attack_types = list(hit.attack_types) + [AttackType.multi_step_jailbreak]
            findings.append(hit)
        if analyser.should_escalate(request.session_id):
            findings.append(
                Finding(
                    id=f"sess_{uuid.uuid4().hex[:8]}",
                    segment_id=segments[0].id if segments else "sess",
                    span=(0, min(40, len(user_blob))),
                    attack_types=[AttackType.multi_step_jailbreak],
                    detector="session",
                    rule_id=None,
                    score=min(1.0, session_risk / max(analyser.threshold, 1e-6)),
                    reason_code="SESSION_ESCALATE",
                    evidence=user_blob[:120],
                )
            )

    max_sev = max((f.score for f in findings if f.detector == "signature"), default=0.0)
    heur = max(
        [f.score for f in findings if f.detector == "heuristic"] + feat_scores,
        default=0.0,
    )
    encoded = 1.0 if any(s.decoded_from for s in segments) else 0.0
    hidden = 1.0 if any(s.location.hidden_reason for s in segments) else 0.0
    pre_score = max(max_sev, heur)
    gate = float(policy.get("classifier_gate", 0.10))

    # Classifier (gated)
    t_clf = time.perf_counter()
    clf_prob = 0.0
    clf = get_classifier()
    if clf is None:
        degraded.append("classifier")
    else:
        for seg in segments:
            run = should_run_classifier(
                pre_score=pre_score,
                gate=gate,
                hidden=bool(seg.location.hidden_reason),
                decoded=bool(seg.decoded_from),
                trust_t1=request.trust == TrustLevel.T1,
            )
            if not run:
                continue
            # Score on original segment text so finding spans keep character offsets.
            raw = seg.text or seg.canonical or ""
            p, win_span = clf.predict_span(raw)
            clf_prob = max(clf_prob, p)
            if p >= 0.55:
                lo, hi = win_span
                # Localised if window is a proper subset of the segment
                localised = hi > lo and (hi - lo) < max(1, int(0.85 * len(raw)))
                if not localised and len(raw) > 0:
                    # Still emit a span for the best window (may be near-full text)
                    lo, hi = win_span if hi > lo else (0, min(len(raw), 200))
                findings.append(
                    Finding(
                        id=f"c_{uuid.uuid4().hex[:8]}",
                        segment_id=seg.id,
                        span=(int(lo), int(hi)),
                        attack_types=[AttackType.instruction_override]
                        + (
                            [AttackType.indirect_injection]
                            if seg.trust.value >= TrustLevel.T2
                            else []
                        ),
                        detector="classifier",
                        rule_id=None,
                        score=float(p),
                        reason_code="CLF_INJECTION" if localised else "CLF_INJECTION_UNLOCALISED",
                        evidence=(raw[lo:hi] if hi > lo else raw)[:200],
                    )
                )
    clf_ms = (time.perf_counter() - t_clf) * 1000

    fusion_cfg = policy.get("fusion") or {}
    pre_risk = fuse_risk(
        max_signature_severity=max_sev,
        heuristic_score=heur,
        classifier_prob=clf_prob,
        hidden=hidden,
        encoded=encoded,
        trust=request.trust,
        session_risk=min(session_risk, 2.0) / 2.0,
        fusion=fusion_cfg,
    )

    # General quotation / educational + human-vs-AI discourse (not exact-match)
    from promptshield.detect.quotation import discourse_features

    quote_text = "\n".join((s.text or "") for s in segments)
    disc = discourse_features(quote_text)
    quote_score = disc.quotation_score
    structural_quote = disc.dampen

    # Judge gray zone (hard timeout so a slow LLM cannot hang the UI)
    t_j = time.perf_counter()
    judge_lo = float((policy.get("judge") or {}).get("lo", 0.35))
    judge_hi = float((policy.get("judge") or {}).get("hi", 0.80))
    # v1.4: 3–5 s hard timeout (default 5000); timeout → unknown, never allow
    timeout_ms = int((policy.get("judge") or {}).get("timeout_ms", 5000))
    timeout_ms = max(3000, min(5000, timeout_ms))
    judge_conf = 0.0
    judge_inj = False
    judge_action: str | None = None
    # Agent-addressed? quotation dampening only applies when NOT agent-directed
    ai_for_live = disc.ai_agent_score if disc.dampen else disc.ai_agent_score_raw
    agent_directed = ai_for_live >= 0.35 or (
        disc.attackish_present
        and ai_for_live >= max(disc.human_reader_score, 0.01)
        and not disc.dampen
    )
    judge_quote = bool(structural_quote) and not agent_directed
    consult_judge = judge_lo <= pre_risk <= judge_hi or (
        request.trust.value <= TrustLevel.T1 and max_sev >= 0.75 and hidden == 0.0
    ) or (structural_quote and max_sev >= 0.5)
    if consult_judge:
        target = max(segments, key=lambda s: len(s.text or ""), default=None)
        if target and (target.text or "").strip():
            jr = None
            try:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    fut = pool.submit(
                        judge_segment,
                        target.text,
                        source_type=request.source_type.value,
                        timeout_ms=timeout_ms,
                    )
                    jr = fut.result(timeout=timeout_ms / 1000.0 + 0.25)
            except (FuturesTimeout, Exception):
                from promptshield.detect.judge import JudgeResult

                jr = JudgeResult(
                    is_injection=False,
                    confidence=0.0,
                    unknown=True,
                    rationale="Judge timeout or error.",
                )
            if jr.unknown:
                if pre_risk >= float(
                    (policy.get("sources") or {}).get(request.source_type.value, {}).get("quarantine", 0.7)
                ):
                    pre_risk = max(pre_risk, 0.7)
            else:
                judge_conf = jr.confidence
                # Quotation from judge lowers risk only for non-agent-addressed content
                if bool(jr.is_quotation_or_discussion) and not agent_directed:
                    judge_quote = True
                judge_inj = bool(jr.is_injection) and not (
                    bool(jr.is_quotation_or_discussion) and not agent_directed
                )
                if judge_inj:
                    span_text = jr.offending_span if jr.offending_span and jr.offending_span in target.text else None
                    if span_text:
                        start = target.text.find(span_text)
                        span = (start, start + len(span_text))
                        judge_action = "sanitize"
                        reason = "JUDGE_INJECTION_SPAN"
                    else:
                        span = (0, min(len(target.text), 200))
                        judge_action = "quarantine"
                        reason = "JUDGE_INJECTION_NO_SPAN"
                    findings.append(
                        Finding(
                            id=f"j_{uuid.uuid4().hex[:8]}",
                            segment_id=target.id,
                            span=span,
                            attack_types=[
                                AttackType(a)
                                for a in jr.attack_types
                                if a in {x.value for x in AttackType}
                            ]
                            or [AttackType.instruction_override],
                            detector="judge",
                            rule_id=None,
                            score=jr.confidence,
                            reason_code=reason,
                            evidence=(span_text or target.text)[:200],
                        )
                    )
    judge_ms = (time.perf_counter() - t_j) * 1000

    risk = fuse_risk(
        max_signature_severity=0.0 if judge_quote else max_sev,
        heuristic_score=0.0 if judge_quote else heur,
        classifier_prob=0.0 if judge_quote else clf_prob,
        judge_confidence=judge_conf,
        judge_says_injection=judge_inj,
        hidden=0.0 if judge_quote else hidden,
        encoded=encoded,
        trust=request.trust,
        session_risk=0.0 if judge_quote else min(session_risk, 2.0) / 2.0,
        fusion=fusion_cfg,
    )
    if not judge_quote and max(max_sev, heur) >= 0.74:
        risk = max(risk, 0.8)
    if "adapter" in degraded and request.trust.value >= TrustLevel.T3:
        risk = max(risk, 0.55)
    if judge_quote and not agent_directed:
        # Lower risk for quotation/discussion only when not agent-addressed
        risk = min(risk, 0.2 if hidden == 0.0 and encoded == 0.0 else 0.45)
        if hidden == 0.0 and encoded == 0.0:
            findings = [f for f in findings if f.detector == "judge"]
    elif agent_directed and (max_sev >= 0.5 or clf_prob >= 0.55 or judge_inj):
        # Agent-addressed live path: do not let quotation collapse signals
        risk = fuse_risk(
            max_signature_severity=max_sev,
            heuristic_score=heur,
            classifier_prob=clf_prob,
            judge_confidence=judge_conf,
            judge_says_injection=judge_inj,
            hidden=hidden,
            encoded=encoded,
            trust=request.trust,
            session_risk=min(session_risk, 2.0) / 2.0,
            fusion=fusion_cfg,
        )
        if max_sev >= 0.75 or clf_prob >= 0.7:
            risk = max(risk, 0.8)

    high_impact = bool(request.agent_context and request.agent_context.high_impact)

    sanitized = None
    spotlighted = None
    reminder = None
    residual_risk = None
    # Provisional decision for redact path
    provisional = decide(
        risk,
        findings,
        trust=request.trust,
        source_type=request.source_type.value,
        text_len=len(redact_base),
        high_impact=high_impact,
        policy=policy,
        max_signature_severity=max_sev,
        judge_action=judge_action,
    )
    if provisional in {Decision.sanitize, Decision.quarantine, Decision.block} and findings:
        primary_findings = [f for f in findings if f.span and f.span[0] < len(redact_base)]
        sanitized = redact_spans(redact_base, primary_findings) if primary_findings else joined
        residual_hits = engine.scan(sanitized)
        residual_h = heuristic_findings(
            adapt(SourceType.text, sanitized, request.trust),
            tools=tools,
        )
        residual_risk = 0.0
        if residual_hits or residual_h:
            residual_risk = max(
                max((f.score for f in residual_hits), default=0.0),
                max((f.score for f in residual_h), default=0.0),
            )
        if _already_sanitized(sanitized):
            residual_risk = 0.0
        if provisional == Decision.block:
            decision = Decision.block
        else:
            decision = decide(
                risk,
                findings,
                trust=request.trust,
                source_type=request.source_type.value,
                text_len=len(redact_base),
                high_impact=high_impact,
                policy=policy,
                residual_risk=residual_risk,
                max_signature_severity=max_sev,
                judge_action=judge_action,
            )
        spotlighted, reminder = spotlight(
            scan_id, request.source_type.value, request.trust.name, sanitized
        )
    else:
        decision = provisional
        if decision == Decision.allow:
            sanitized = redact_base

    if "ocr_unavailable" in degraded and request.source_type == SourceType.image and not findings:
        decision = Decision.quarantine
        degraded = list(dict.fromkeys(degraded))

    attack_types = sorted({a for f in findings for a in f.attack_types}, key=lambda x: x.value)
    total_ms = (time.perf_counter() - t0) * 1000
    return ScanResult(
        scan_id=scan_id,
        decision=decision,
        risk=round(risk, 4),
        attack_types=attack_types,
        findings=findings,
        segments=_segment_summaries(segments),
        sanitized_text=sanitized,
        spotlighted_text=spotlighted,
        system_reminder=reminder,
        hidden_content_revealed=any(s.location.hidden_reason for s in segments),
        latency_ms={
            "adapt": round(adapt_ms, 3),
            "signatures": round(sig_ms, 3),
            "classifier": round(clf_ms, 3),
            "judge": round(judge_ms, 3),
            "total": round(total_ms, 3),
        },
        policy_version=str(policy.get("version", "1")),
        degraded=list(dict.fromkeys(degraded)),
    )


def scan_text(text: str, source_type: SourceType = SourceType.text) -> ScanResult:
    return scan(ScanRequest(source_type=source_type, content=text, trust=TrustLevel.T3), noop=False)


def scan_file_bytes(
    data: bytes,
    source_type: SourceType,
    *,
    trust: TrustLevel = TrustLevel.T3,
) -> ScanResult:
    return scan(
        ScanRequest(source_type=source_type, content=None, trust=trust),
        noop=False,
        raw=data,
    )
