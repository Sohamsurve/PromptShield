"""Context taint and argument provenance (README §5.10)."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from promptshield.domain import ContextItem, TrustLevel

SENSITIVE_KEYS = {
    "to",
    "recipient",
    "email",
    "url",
    "path",
    "command",
    "amount",
    "body",
    "content",
    "note",
}


def context_tainted(context: list[ContextItem], *, threshold: float = 0.3) -> bool:
    for item in context:
        if item.trust.value >= TrustLevel.T2 and item.risk >= threshold:
            return True
    return False


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def untrusted_arguments(
    args: dict,
    context: list[ContextItem],
    user_goal: str | None,
    *,
    sensitive_keys: set[str] | None = None,
) -> list[str]:
    """Values that appear only in T2/T3 context, not in T0/T1 or user_goal."""
    keys = sensitive_keys or SENSITIVE_KEYS
    trusted_blob = " ".join(
        _norm(i.text or "") for i in context if i.trust.value <= TrustLevel.T1
    )
    if user_goal:
        trusted_blob += " " + _norm(user_goal)
    untrusted_blob = " ".join(
        _norm(i.text or "") for i in context if i.trust.value >= TrustLevel.T2
    )

    tainted: list[str] = []
    for key, raw in args.items():
        if key not in keys:
            continue
        val = _norm(str(raw))
        if not val:
            continue
        # email / url special: extract host
        candidates = [val]
        if "@" in val:
            candidates.append(val)
        if val.startswith("http"):
            try:
                candidates.append(urlparse(val).netloc.lower())
            except Exception:
                pass
        in_trusted = any(c and c in trusted_blob for c in candidates)
        in_untrusted = any(c and c in untrusted_blob for c in candidates)
        if in_untrusted and not in_trusted:
            tainted.append(str(raw))
        # Also: if no trusted context at all and untrusted context exists and value looks like email/url
        if not trusted_blob.strip() and untrusted_blob and ("@" in val or val.startswith("http") or val.startswith(".")):
            if str(raw) not in tainted:
                tainted.append(str(raw))
    return tainted
