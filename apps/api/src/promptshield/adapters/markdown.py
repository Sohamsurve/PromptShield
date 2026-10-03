"""Markdown adapter — link titles, comments, HTML blocks."""

from __future__ import annotations

import re

from promptshield.adapters import html as html_adapter
from promptshield.adapters.common import make_segment
from promptshield.domain import Segment, TrustLevel

_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
_COMMENT_RE = re.compile(r"<!--([\s\S]*?)-->")
_HTML_BLOCK_RE = re.compile(r"(?is)<(div|span|p|html|body|table)[\s>][\s\S]*?</\1>")


def extract(text: str, source_id: str, trust: TrustLevel) -> list[Segment]:
    segs: list[Segment] = []

    # Visible-ish: strip link titles for main body preview
    visible = _COMMENT_RE.sub("", text)
    visible = _LINK_RE.sub(lambda m: m.group(1) or m.group(2), visible)
    segs.append(make_segment(source_id=source_id, text=visible.strip(), trust=trust, kind="visible"))

    for m in _COMMENT_RE.finditer(text):
        body = m.group(1).strip()
        if body:
            segs.append(
                make_segment(
                    source_id=source_id,
                    text=body,
                    trust=trust,
                    kind="comment",
                    hidden_reason="html:comment",
                )
            )

    for m in _LINK_RE.finditer(text):
        title = m.group(3)
        if title:
            segs.append(
                make_segment(
                    source_id=source_id,
                    text=title,
                    trust=trust,
                    kind="hidden",
                    hidden_reason="md:link_title",
                    path=m.group(2),
                )
            )
        alt = m.group(1)
        if alt:
            segs.append(
                make_segment(source_id=source_id, text=alt, trust=trust, kind="alt_text", path=m.group(2))
            )

    # HTML blocks → HTML adapter
    for m in _HTML_BLOCK_RE.finditer(text):
        segs.extend(html_adapter.extract(m.group(0), source_id, trust))

    # front matter
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end].strip()
            if fm:
                segs.append(
                    make_segment(
                        source_id=source_id,
                        text=fm,
                        trust=trust,
                        kind="metadata",
                        path="front_matter",
                    )
                )

    return segs
