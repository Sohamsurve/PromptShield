"""Secret / PII scanners for output guard."""

from __future__ import annotations

import math
import re
from collections import Counter

_PATTERNS = [
    (re.compile(r"(?i)-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"), "SECRET_PRIVATE_KEY"),
    (re.compile(r"(?i)\b(api[_-]?key|secret|token)\b\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"), "SECRET_KEY_ASSIGN"),
    (re.compile(r"\bCANARY-[a-f0-9]{8,}\b"), "CANARY_TOKEN"),
    (re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"), "EMAIL_ADDR"),
]


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def find_secrets(text: str) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    for pat, code in _PATTERNS:
        for m in pat.finditer(text or ""):
            hits.append((code, m.group(0)[:80]))
    # High-entropy token heuristic
    for tok in re.findall(r"[A-Za-z0-9_\-/+]{32,}", text or ""):
        if shannon_entropy(tok) >= 4.0 and not tok.startswith("http"):
            hits.append(("SECRET_ENTROPY", tok[:80]))
    return hits


def ngram_overlap(text: str, reference: str, n: int = 8) -> bool:
    def grams(s: str) -> set[str]:
        s = re.sub(r"\s+", " ", s.lower())
        words = s.split()
        if len(words) < n:
            return set()
        return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}

    a, b = grams(text), grams(reference)
    return bool(a & b)
