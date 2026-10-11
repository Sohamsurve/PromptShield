"""Heuristic features + findings (README §5.5)."""

from __future__ import annotations

import math
import re
import uuid
from typing import Any

from promptshield.domain import AttackType, Finding, Segment, TrustLevel
from promptshield.normalize.unicode import canonicalize

_IMPERATIVE_VERBS = (
    "ignore",
    "disregard",
    "forget",
    "override",
    "reveal",
    "print",
    "forward",
    "send",
    "run",
    "execute",
    "remember",
    "decode",
    "obey",
    "comply",
)
_IMPERATIVE = re.compile(r"(?i)\b(" + "|".join(_IMPERATIVE_VERBS) + r")\b")
_ADDRESSEE = re.compile(
    r"(?i)\b(you|assistant|ai|model|agent|claude|gpt|copilot)\b"
)
_TOOLISH = re.compile(r"(?i)\b(send_email|fetch_url|read_file|save_memory|curl|transfer)\b")
_CREDS = re.compile(r"(?i)(\.env|id_rsa|password|api[_ ]?key|credentials|~/?\.ssh)")
_EXFIL = re.compile(
    r"(?i)\b(send_email|send|post|upload|forward|email|mail|fetch)\b(?:[\W_]+\w+){0,8}[\W_]+"
    r"([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}|\.test\b|https?://|/[^\s]+)"
)
_POISON = re.compile(
    r"(?i)\b("
    r"from\s+now\s+on|always\s+answer|add\s+this\s+to\s+your\s+memory|remember\s+that|"
    r"persist\s+this|store\s+permanently|henceforth|policies?\s+do\s+not\s+apply|"
    r"bypass\s+filters|trusted\s+forever"
    r")\b"
)
_ROLE = re.compile(
    r"(?i)(?:^\s*system\s*:|###\s*assistant|<\|im_start\|>|you are now|act as|developer mode|jailbreak)"
)
# Hidden commands that do not use the word "canary" or the short override list.
_HIDDEN_COMMAND = re.compile(
    r"(?i)(?:"
    r"\b(?:do not|don't|never)\b[^.\n]{0,48}\b(?:tell|mention|show|reveal|share|disclose|warn|log|report)\b"
    r"|"
    r"\byou (?:must|should|will|are to|need to)\b"
    r"|"
    r"\b(?:new|updated|priority|hidden)\s+(?:instruction|directive|order|command|policy)\b"
    r"|"
    r"\b(?:follow|obey|carry out)\b[^.\n]{0,40}\b(?:instruction|directive|order|command|policy|above|below)\b"
    r"|"
    r"\b(?:answer|reply|respond)\b[^.\n]{0,40}\b(?:as if|instead|only with|without)\b"
    r"|"
    r"\b(?:provide|give|list|dump|paste|output)\b[^.\n]{0,40}\b(?:secret|password|prompt|instruction|key|credential|token)s?\b"
    r")"
)


def looks_like_hidden_command(text: str) -> bool:
    """A hidden line is a command when it tells the model what to do.

    The word "canary" is not required. A revenue sentence is not a command.
    """
    if _IMPERATIVE.search(text) or _TOOLISH.search(text) or _CREDS.search(text):
        return True
    if _EXFIL.search(text) or _POISON.search(text) or _ROLE.search(text):
        return True
    return _HIDDEN_COMMAND.search(text) is not None
_DATA_CTX = re.compile(r"(?i)\b(invoice|order|recipe|changelog|meeting|agenda|quarterly)\b")


def compute_features(
    seg: Segment,
    *,
    tools: list[str] | None = None,
    invisible_chars: int | None = None,
) -> dict[str, float]:
    text = seg.text or ""
    tokens = re.findall(r"\w+", text.lower())
    n = max(len(tokens), 1)
    imperatives = len(_IMPERATIVE.findall(text))
    addressees = len(_ADDRESSEE.findall(text))
    # addressee near imperatives: crude window density
    addressee = min(1.0, (addressees / n) * 8.0) if imperatives else min(1.0, addressees / n)
    imperative_density = min(1.0, (imperatives / n) * 100.0 / 20.0)  # scale ~20/100tok → 1

    tools = tools or []
    tool_hits = 0
    low = text.lower()
    for t in tools:
        if t.lower() in low:
            tool_hits += 1
    if _TOOLISH.search(text):
        tool_hits += 1
    tool_mentions = min(1.0, tool_hits / max(len(tools), 1))

    exfil_shape = 1.0 if _EXFIL.search(text) else 0.0
    role_markers = 1.0 if _ROLE.search(text) else 0.0
    hidden = 1.0 if seg.location.hidden_reason else 0.0
    encoded = 1.0 if seg.decoded_from else 0.0
    if invisible_chars is None:
        invisible_chars = int(canonicalize(text).features.get("invisible_chars", 0))
    inv = min(1.0, math.log1p(invisible_chars) / math.log1p(20))
    instruction_in_data = (
        1.0 if (_DATA_CTX.search(text) and imperatives > 0 and _IMPERATIVE.search(text)) else 0.0
    )
    trust_prior = {TrustLevel.T0: 0.0, TrustLevel.T1: 0.33, TrustLevel.T2: 0.66, TrustLevel.T3: 1.0}.get(
        seg.trust, 1.0
    )

    from promptshield.detect.quotation import discourse_features

    disc = discourse_features(text)
    return {
        "addressee": float(addressee),
        "imperative_density": float(imperative_density),
        "tool_mentions": float(tool_mentions),
        "exfil_shape": float(exfil_shape),
        "role_markers": float(role_markers),
        "hidden": float(hidden),
        "encoded": float(encoded),
        "invisible_chars": float(inv),
        "instruction_in_data": float(instruction_in_data),
        "trust_prior": float(trust_prior),
        "quotation_score": float(disc.quotation_score),
        "educational_score": float(disc.educational_score),
        "human_reader_score": float(disc.human_reader_score),
        "ai_agent_score": float(disc.ai_agent_score),
    }


def heuristic_score(features: dict[str, float]) -> float:
    """Aggregate [0,1] score for fusion pre-gate."""
    weights = {
        "addressee": 0.1,
        "imperative_density": 0.15,
        "tool_mentions": 0.15,
        "exfil_shape": 0.2,
        "role_markers": 0.15,
        "hidden": 0.1,
        "encoded": 0.05,
        "invisible_chars": 0.05,
        "instruction_in_data": 0.05,
    }
    score = sum(features.get(k, 0.0) * w for k, w in weights.items())
    if features.get("hidden", 0) and features.get("imperative_density", 0) > 0:
        score = min(1.0, score + 0.15)
    # Dampen when discourse looks human/educational rather than AI-directed
    q = features.get("quotation_score", 0.0)
    human = features.get("human_reader_score", 0.0)
    ai = features.get("ai_agent_score", 0.0)
    if q >= 0.55 or (human > ai and human >= 0.45 and features.get("educational_score", 0) >= 0.35):
        score *= 0.25
    return max(0.0, min(1.0, score))


def heuristic_findings(segments: list[Segment], *, tools: list[str] | None = None) -> list[Finding]:
    out: list[Finding] = []
    for seg in segments:
        text = seg.text or ""
        if not text.strip():
            continue
        # Skip our own redaction markers
        if text.strip().startswith("[removed:"):
            continue

        feats = compute_features(seg, tools=tools)
        hidden = bool(seg.location.hidden_reason)
        risky_json = (seg.location.hidden_reason or "") == "json:risky_key"
        special_kind = seg.location.kind in {"comment", "alt_text", "metadata", "ocr"}
        untrusted = seg.trust.value >= TrustLevel.T2

        trigger = False
        types: list[AttackType] = []

        if hidden and looks_like_hidden_command(text):
            trigger = True
            types.append(AttackType.instruction_override)
        elif (risky_json or special_kind) and (
            _IMPERATIVE.search(text) or _TOOLISH.search(text) or _CREDS.search(text)
        ):
            trigger = True
            types.append(AttackType.instruction_override)

        if untrusted and (feats["tool_mentions"] > 0 or feats["exfil_shape"] > 0):
            trigger = True
            types.append(AttackType.tool_abuse)

        if untrusted and _CREDS.search(text):
            trigger = True
            types.append(AttackType.credential_theft)

        if _POISON.search(text) and (
            untrusted
            or re.search(
                r"(?i)\b(?:always\s+answer|persist\s+this|store\s+permanently|"
                r"from\s+now\s+on\s+always|policies?\s+do\s+not\s+apply|"
                r"add\s+this\s+to\s+your\s+memory|trusted\s+forever|bypass\s+filters)\b",
                text,
            )
        ):
            trigger = True
            types.append(AttackType.context_poisoning)

        if feats["role_markers"] > 0 and untrusted:
            trigger = True
            types.append(AttackType.role_change)

        if not trigger:
            continue

        uniq: list[AttackType] = []
        for t in types:
            if t not in uniq:
                uniq.append(t)
        if untrusted and AttackType.indirect_injection not in uniq:
            uniq.append(AttackType.indirect_injection)

        score = max(0.74, heuristic_score(feats))
        out.append(
            Finding(
                id=f"h_{uuid.uuid4().hex[:8]}",
                segment_id=seg.id,
                span=(0, min(len(text), 200)),
                attack_types=uniq or [AttackType.instruction_override],
                detector="heuristic",
                rule_id=None,
                score=min(1.0, score),
                reason_code="HIDDEN_IMPERATIVE" if (hidden or special_kind) else "EXFIL_SHAPE",
                evidence=text[:200],
            )
        )
    return out
