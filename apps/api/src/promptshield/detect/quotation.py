"""General quotation / discussion / educational framing detector (not exact-match allowlists)."""

from __future__ import annotations

import re

# Framing that indicates the attack phrase is being *discussed*, not issued as an instruction.
_FRAME_RES = [
    re.compile(r"(?i)\b(?:security\s+article|blog\s+post|tutorial|textbook|paper|lecture|course)\b"),
    re.compile(r"(?i)\b(?:attackers?\s+(?:sometimes|often|may|will)|adversaries?\s+may)\b"),
    re.compile(r"(?i)\b(?:quoting|quoted|quotation|for\s+example|e\.g\.|such\s+as)\b"),
    re.compile(r"(?i)\b(?:defenders?\s+should|treat\s+(?:that|this|it)\s+as\s+data)\b"),
    re.compile(r"(?i)\b(?:educational|illustrative|hypothetical\s+example)\b"),
    re.compile(r"(?i)\b(?:discussion\s+of|analysis\s+of)\s+(?:prompt\s+)?injection\b"),
    re.compile(r"(?i)\b(?:phrases?\s+like|strings?\s+like|pattern\s+like)\b"),
    re.compile(r"(?i)\b(?:do\s+not\s+follow|should\s+not\s+obey|must\s+not\s+execute)\b"),
]

_ATTACKISH = re.compile(
    r"(?i)\b(?:ignore\s+previous|disregard\s+prior|override\s+all|"
    r"system\s+prompt|jailbreak|send_email|from\s+now\s+on)\b"
)


def quotation_or_discussion_score(text: str) -> float:
    """Return [0,1] confidence that attack-like spans are framed as quotation/education."""
    if not text or not _ATTACKISH.search(text):
        return 0.0
    hits = sum(1 for r in _FRAME_RES if r.search(text))
    if hits == 0:
        return 0.0
    # Stronger when multiple independent framing cues appear
    return min(1.0, 0.35 + 0.2 * hits)


def is_quotation_or_discussion(text: str, *, threshold: float = 0.55) -> bool:
    return quotation_or_discussion_score(text) >= threshold
