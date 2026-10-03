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

# User asked to act on a value found in content (not a general taint loosen).
_USER_REPLY = re.compile(
    r"(?i)\b(?:reply\s+to\s+this\s+email|email\s+(?:them|him|her|the\s+(?:sender|contact|person))|"
    r"forward\s+this\s+(?:file|document|email|message)\s+to\s+the\s+person|"
    r"send\s+(?:this|it)\s+to\s+the\s+(?:person|address|contact)\s+named|"
    r"mail\s+(?:the\s+)?(?:person|contact)\s+(?:named|in\s+this)|"
    r"use\s+the\s+(?:address|email)\s+in\s+this)\b"
)
_USER_OPEN_LINK = re.compile(
    r"(?i)\b(?:open\s+the\s+link\s+in\s+this|visit\s+the\s+url\s+in\s+this|"
    r"fetch\s+the\s+(?:link|url)\s+(?:from|in)\s+this|follow\s+the\s+link\s+in\s+this)\b"
)
_USER_OPEN_FILE = re.compile(
    r"(?i)\b(?:open\s+the\s+(?:file|attachment|path)\s+in\s+this|"
    r"read\s+the\s+file\s+(?:named|mentioned)\s+in\s+this)\b"
)


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


def user_requested_arg_provenance(
    tool: str,
    args: dict,
    user_goal: str | None,
    context: list[ContextItem],
) -> list[str]:
    """Return arg values the user's instruction explicitly asked to use from content.

    Does not clear taint generally — only when the user requested that action class.
    """
    goal = (user_goal or "").strip()
    # Also consult T0/T1 context text as the user instruction channel
    for item in context:
        if item.trust.value <= TrustLevel.T1 and item.text:
            goal = (goal + " " + item.text).strip()
    if not goal:
        return []

    authorized: list[str] = []
    if tool == "send_email" and _USER_REPLY.search(goal):
        to = str(args.get("to") or args.get("recipient") or args.get("email") or "")
        if to:
            authorized.append(to)
    if tool == "fetch_url" and _USER_OPEN_LINK.search(goal):
        url = str(args.get("url") or "")
        if url:
            authorized.append(url)
    if tool == "read_file" and _USER_OPEN_FILE.search(goal):
        path = str(args.get("path") or "")
        if path:
            authorized.append(path)
    return authorized
