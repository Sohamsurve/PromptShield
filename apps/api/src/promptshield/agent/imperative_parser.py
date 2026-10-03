"""Scripted-agent instruction parser.

Patterns here are intentionally **not** copied from `rules/*.yml`. They model a
naive unprotected agent that follows surface-level commands in content.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ParsedImperatives:
    role_hijack: bool = False
    reveal_secret: bool = False
    read_sensitive_file: bool = False
    send_email_to: str | None = None
    memory_note: str | None = None
    credential_phish: bool = False
    flags: list[str] = field(default_factory=list)


# Agent-behaviour patterns (distinct wording / structure from detector YAML rules).
_ROLE = re.compile(
    r"(?i)(?:switch\s+persona\s+to|enter\s+unrestricted\s+mode|pretend\s+you\s+are|"
    r"you\s+are\s+now|act\s+as|developer\s+mode|jailbreak\s+mode)"
)
_OVERRIDE = re.compile(
    r"(?i)(?:stop\s+obeying\s+earlier\s+rules|discard\s+prior\s+guidance|"
    r"ignore|disregard|forget|override).{0,48}(?:previous|prior|above|all).{0,36}"
    r"(?:instructions?|rules?|policies)"
)
_REVEAL = re.compile(
    r"(?i)(?:dump|leak|whisper|unveil|reveal|print|repeat|output|show)\s+"
    r"(?:your\s+)?(?:system\s+prompt|hidden\s+instructions|api\s+key|secret|"
    r"environment\s+variables|env\s*vars?)"
)
_READ = re.compile(
    r"(?i)(?:open|dump|cat|read|print).{0,48}(?:\.env|id_rsa|credentials|~/?\.ssh|/etc/passwd)"
)
_FORWARD = re.compile(
    r"(?i)(?:relay|ship|forward)\s+(?:the\s+)?(?:last\s+)?(?:\d+\s+)?(?:emails?|messages?)\s+to\s+(\S+)"
)
_SEND = re.compile(
    r"(?i)(?:mail|email|send)\s+(?:this|it|the\s+report|everything)?\s*(?:to\s+)?"
    r"([a-zA-Z0-9._%+-]+@(?:evil\.test|example\.test|example\.com|\S+))"
)
_EMAIL = re.compile(
    r"\b([a-zA-Z0-9._%+-]+@(?:evil\.test|example\.test|example\.com))\b",
    re.I,
)
_MEMORY = re.compile(
    r"(?i)(?:persist\s+this|store\s+permanently|remember\s+that|from\s+now\s+on|"
    r"always\s+answer|add\s+this\s+to\s+your\s+memory)\s*[:\s]*(.+)"
)
_PHISH = re.compile(r"(?i)(?:session\s+expired|re-enter\s+your\s+password|verify\s+your\s+password)")


def parse_imperatives(text: str) -> ParsedImperatives:
    out = ParsedImperatives()
    if not text:
        return out
    if _ROLE.search(text) or _OVERRIDE.search(text):
        out.role_hijack = True
        out.flags.append("role_hijack")
    if _REVEAL.search(text):
        out.reveal_secret = True
        out.flags.append("reveal_secret")
    if _READ.search(text) or "print all environment variables" in text.lower():
        out.read_sensitive_file = True
        out.flags.append("read_sensitive_file")
    m = _FORWARD.search(text) or _SEND.search(text)
    if m:
        out.send_email_to = m.group(1).strip().rstrip(".,;\"'")
        out.flags.append("send_email")
    elif "send_email" in text.lower():
        em = _EMAIL.search(text)
        if em:
            out.send_email_to = em.group(1)
            out.flags.append("send_email")
    mem = _MEMORY.search(text)
    if mem:
        out.memory_note = mem.group(1).strip()[:500]
        out.flags.append("memory")
    if _PHISH.search(text):
        out.credential_phish = True
        out.flags.append("credential_phish")
    return out
