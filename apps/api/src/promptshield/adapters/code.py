"""Source-code adapter — comments, docstrings, string literals."""

from __future__ import annotations

import re

from promptshield.adapters.common import make_segment
from promptshield.domain import Segment, TrustLevel

_LINE_COMMENT = re.compile(r"(?m)#(.*)$|//(.*)$")
_BLOCK_COMMENT = re.compile(r"/\*([\s\S]*?)\*/")
_DOCSTRING = re.compile(r'(?s)"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\'')
_STRING = re.compile(r'(?P<q>["\'])(?P<body>(?:\\.|(?!\1).)*)(?P=q)')
_AI_ADDR = re.compile(r"(?i)\b(ai|assistant|agent|copilot|claude|gpt)\b")


def extract(text: str, source_id: str, trust: TrustLevel) -> list[Segment]:
    segs: list[Segment] = [
        make_segment(source_id=source_id, text=text, trust=trust, kind="visible", path="source")
    ]

    for m in _LINE_COMMENT.finditer(text):
        body = (m.group(1) or m.group(2) or "").strip()
        if not body:
            continue
        reason = "code:ai_comment" if _AI_ADDR.search(body) else None
        segs.append(
            make_segment(
                source_id=source_id,
                text=body,
                trust=trust,
                kind="comment",
                hidden_reason=reason,
            )
        )

    for m in _BLOCK_COMMENT.finditer(text):
        body = m.group(1).strip()
        if body:
            segs.append(
                make_segment(
                    source_id=source_id,
                    text=body,
                    trust=trust,
                    kind="comment",
                    hidden_reason="code:ai_comment" if _AI_ADDR.search(body) else None,
                )
            )

    for m in _DOCSTRING.finditer(text):
        body = (m.group(1) or m.group(2) or "").strip()
        if body:
            segs.append(make_segment(source_id=source_id, text=body, trust=trust, kind="comment"))

    for m in _STRING.finditer(text):
        body = m.group("body")
        if len(body) >= 12 and re.search(r"(?i)\b(ignore|instruction|system prompt|send_email)\b", body):
            segs.append(
                make_segment(
                    source_id=source_id,
                    text=body,
                    trust=trust,
                    kind="hidden",
                    hidden_reason="code:string_instruction",
                )
            )

    return segs
