"""Scan pipeline — adapt → canonicalise/decode → signatures → fuse → neutralise."""

from __future__ import annotations

import os
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
from promptshield.neutralize.redact import document_redact_findings, redact_spans, safe_alternative, spotlight
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
    from promptshield.detect.cascade import prefilter_score, run_chunked_judge

    casc = (policy.get("judge") or {}).get("cascade") or {}
    cascade_env = (os.getenv("JUDGE_CASCADE") or "").strip().lower()
    cascade_forced_off = cascade_env in {"0", "false", "no"}
    cascade_forced_on = cascade_env in {"1", "true", "yes"}
    from promptshield.detect.judge import judge_config

    # Live key → full cascade is the default. Offline stays on the policy flag.
    live_judge = judge_config().get("judge_mode") == "live"
    cascade_on = False if cascade_forced_off else (
        cascade_forced_on or bool(casc.get("enabled")) or live_judge
    )
    gray_only = (os.getenv("JUDGE_GRAY_ZONE_ONLY") or "").strip() in {"1", "true", "yes"}
    judge_disabled = (os.getenv("JUDGE_DISABLE") or "").strip() in {"1", "true", "yes"}
    pref = prefilter_score(max_sev=max_sev, heur=heur, clf_prob=clf_prob)
    pref_thr = float(casc.get("prefilter_threshold", 0.15))
    pref_hi = float(casc.get("prefilter_hi", 0.55))

    long_doc = sum(len(s.text or "") for s in segments) >= 1500
    in_gray_band = judge_lo <= pre_risk <= judge_hi
    # Second look: an image still in doubt, with faint ink Tesseract did not read.
    if (
        request.source_type == SourceType.image
        and isinstance(raw, (bytes, bytearray))
        and in_gray_band
    ):
        from promptshield.adapters.vision_ocr import instruction_recovered, supplement_unresolved

        if segments and not instruction_recovered(segments):
            extra = supplement_unresolved(
                bytes(raw),
                segments,
                source_id=segments[0].source_id,
                trust=request.trust,
            )
            if extra:
                segments.extend(extra)
                for seg in extra:
                    hay = seg.canonical or seg.text
                    for h in engine.scan(hay, segment_id=seg.id):
                        if (
                            seg.trust.value >= TrustLevel.T2
                            and AttackType.indirect_injection not in h.attack_types
                        ):
                            h.attack_types = list(h.attack_types) + [AttackType.indirect_injection]
                        findings.append(h)
                findings.extend(heuristic_findings(extra, tools=tools))
                max_sev = max((f.score for f in findings if f.detector == "signature"), default=0.0)
                hidden = 1.0 if any(s.location.hidden_reason for s in segments) else 0.0
    consult_judge = in_gray_band or (
        request.trust.value <= TrustLevel.T1 and max_sev >= 0.75 and hidden == 0.0
    ) or (structural_quote and max_sev >= 0.5)
    if gray_only:
        consult_judge = in_gray_band
        cascade_on = False
    if cascade_on:
        # Full cascade: anything above prefilter (or long text) goes to chunked judge
        consult_judge = pref >= pref_thr or long_doc or consult_judge
    if judge_disabled:
        consult_judge = False
        cascade_on = False

    judge_calls = 0
    judge_chunks = 0
    consult_reason = "none"
    if consult_judge:
        if cascade_on and (pref >= pref_thr or long_doc):
            consult_reason = "cascade_prefilter" if pref >= pref_thr else "cascade_long_doc"
        elif in_gray_band:
            consult_reason = "gray_band"
        elif structural_quote and max_sev >= 0.5:
            consult_reason = "structural_quote"
        else:
            consult_reason = "high_sig_t1"

    if consult_judge:
        target = max(segments, key=lambda s: len(s.text or ""), default=None)
        if target and (target.text or "").strip():
            if cascade_on and max_sev < 0.75:
                from promptshield.detect.cascade import chunk_offsets

                judge_chunks = len(chunk_offsets(target.text))
                judge_calls += judge_chunks
                action, spans, _unk = run_chunked_judge(
                    target.text,
                    source_type=request.source_type.value,
                    judge_fn=judge_segment,
                    timeout_ms=timeout_ms,
                    prefilter=pref,
                    prefilter_hi=pref_hi,
                )
                if action == "sanitize" and spans:
                    judge_inj = True
                    judge_conf = max(judge_conf, 0.8)
                    judge_action = "sanitize"
                    for lo, hi in spans[:8]:
                        findings.append(
                            Finding(
                                id=f"j_{uuid.uuid4().hex[:8]}",
                                segment_id=target.id,
                                span=(lo, hi),
                                attack_types=[AttackType.instruction_override],
                                detector="judge",
                                rule_id=None,
                                score=0.8,
                                reason_code="JUDGE_INJECTION_SPAN",
                                evidence=target.text[lo:hi][:200],
                            )
                        )
                elif action == "quarantine":
                    judge_inj = True
                    judge_conf = max(judge_conf, 0.75)
                    judge_action = "quarantine"
                    findings.append(
                        Finding(
                            id=f"j_{uuid.uuid4().hex[:8]}",
                            segment_id=target.id,
                            span=(0, min(len(target.text), 200)),
                            attack_types=[AttackType.instruction_override],
                            detector="judge",
                            rule_id=None,
                            score=0.75,
                            reason_code="JUDGE_INJECTION_NO_SPAN",
                            evidence=target.text[:200],
                        )
                    )
            else:
                judge_calls += 1
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
                    # never allow because of an error — quarantine if prefilter high
                    if pref >= pref_hi or pre_risk >= float(
                        (policy.get("sources") or {})
                        .get(request.source_type.value, {})
                        .get("quarantine", 0.7)
                    ):
                        judge_action = "quarantine"
                        judge_inj = True
                        pre_risk = max(pre_risk, 0.7)
                else:
                    judge_conf = jr.confidence
                    # A discussion flag cannot erase a signature the structural
                    # quotation check did not already dampen. The judge never
                    # overrides a real instruction on its own.
                    if (
                        bool(jr.is_quotation_or_discussion)
                        and not agent_directed
                        and structural_quote
                    ):
                        judge_quote = True
                    judge_inj = bool(jr.is_injection) and not (
                        bool(jr.is_quotation_or_discussion) and not agent_directed
                    )
                    if judge_inj:
                        span_text = (
                            jr.offending_span
                            if jr.offending_span and jr.offending_span in target.text
                            else None
                        )
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
        if content:
            primary_findings = [
                f
                for f in findings
                if f.span
                and f.span[0] < len(redact_base)
                and f.reason_code != "CLF_INJECTION_UNLOCALISED"
            ]
        else:
            primary_findings = document_redact_findings(segments, findings, redact_base)
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

    # README §5.1: OCR failure → quarantine images (cannot verify hidden text).
    # Do not let a classifier hit on the placeholder string keep decision=allow.
    if "ocr_unavailable" in degraded and request.source_type == SourceType.image:
        if decision == Decision.allow:
            decision = Decision.quarantine
        degraded = list(dict.fromkeys(degraded))

    # An acted decision must not display a near-zero fused risk. The number
    # shown is at least the score of the finding that justified the action.
    # Rounding to 4 decimals must not drop the displayed value below that score.
    if decision != Decision.allow and findings:
        driver = max(float(f.score) for f in findings)
        risk = max(risk, driver)
        shown = round(risk, 4)
        if shown < driver:
            shown = (int(driver * 10000) + 1) / 10000
        risk = shown
    else:
        risk = round(risk, 4)

    from promptshield.adapters.vision_ocr import consume_vision_degraded
    from promptshield.detect.judge import consume_judge_degraded

    degraded.extend(consume_judge_degraded())
    degraded.extend(consume_vision_degraded())

    attack_types = sorted({a for f in findings for a in f.attack_types}, key=lambda x: x.value)
    total_ms = (time.perf_counter() - t0) * 1000
    from promptshield import scan_telemetry

    scan_telemetry.record(
        consult_judge=consult_judge,
        consult_reason=consult_reason,
        cascade_on=cascade_on,
        judge_disabled=judge_disabled,
        gray_zone_only=gray_only,
        pre_risk=round(pre_risk, 4),
        pref=round(pref, 4),
        judge_calls=judge_calls,
        judge_chunks=judge_chunks,
        long_doc=long_doc,
        in_gray_band=in_gray_band,
    )
    _dedupe_finding_ids(findings)
    return ScanResult(
        scan_id=scan_id,
        decision=decision,
        risk=risk,
        attack_types=attack_types,
        findings=findings,
        segments=_segment_summaries(segments),
        sanitized_text=sanitized,
        spotlighted_text=spotlighted,
        safe_alternative=safe_alternative(decision.value, sanitized, residual_risk=residual_risk),
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


def _dedupe_finding_ids(findings: list[Finding]) -> None:
    """Signature scans restart their counter per segment, so stored rows can repeat f1."""
    seen: set[str] = set()
    for index, finding in enumerate(findings):
        base = finding.id or f"f{index}"
        candidate = base
        n = 2
        while candidate in seen:
            candidate = f"{base}-{n}"
            n += 1
        finding.id = candidate
        seen.add(candidate)


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
